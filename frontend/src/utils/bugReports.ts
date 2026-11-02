export type BugReportCandidate = {
  id: string
  title: string
  description: string
}

type Heading = {
  level: number
  title: string
  line: number
}

const GENERIC_BUG_HEADINGS = /^(?:bug reports?|defects?|findings|summary|overview|details)$/i

function cleanTitle(value: string): string {
  return value
    .replace(/^\s*(?:bug|defect)\s*(?:report\s*)?(?:#?\d+\s*)?[:.)\-–—]\s*/i, '')
    .replace(/^\s*\d+[.)]\s*/, '')
    .replace(/^\s*\*\*|\*\*\s*$/g, '')
    .replace(/\*\*/g, '')
    .replace(/`/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function makeCandidate(
  titleValue: string,
  lines: string[],
  id: number,
  descriptionOverride?: string,
): BugReportCandidate | null {
  const title = cleanTitle(titleValue)
  if (!title || GENERIC_BUG_HEADINGS.test(title)) return null
  const description = (descriptionOverride ?? lines.join('\n')).trim().slice(0, 20000)
  return {
    id: `${id}-${title.toLowerCase()}`,
    title: title.slice(0, 255),
    description: description || title,
  }
}

function parseHeadings(lines: string[]): Heading[] {
  return lines.flatMap((line, index) => {
    const match = /^(#{2,6})\s+(.+?)\s*#*\s*$/.exec(line)
    return match ? [{ level: match[1].length, title: match[2], line: index }] : []
  })
}

export function extractBugReports(markdown: string): BugReportCandidate[] {
  const lines = markdown.split(/\r?\n/)
  const headings = parseHeadings(lines)
  const candidates: BugReportCandidate[] = []
  const addCandidate = (
    title: string,
    start: number,
    end: number,
    descriptionOverride?: string,
  ) => {
    const body = lines.slice(start, end)
    const candidate = makeCandidate(title, body, candidates.length + 1, descriptionOverride)
    if (candidate && !candidates.some((existing) => existing.title === candidate.title)) {
      candidates.push(candidate)
    }
  }

  const bugHeadingPattern =
    /^\s*(?:#{2,6}\s*)?(?:\*\*)?(?:bug|defect)\s*(?:report\s*)?#?\s*\d+\s*[.):\-–—]\s*(.+?)(?:\*\*)?\s*$/i
  const bugTitleLines = lines.flatMap((line, index) => {
    const match = bugHeadingPattern.exec(line)
    return match ? [{ title: match[1], line: index }] : []
  })

  if (bugTitleLines.length > 0) {
    for (let index = 0; index < bugTitleLines.length; index += 1) {
      const current = bugTitleLines[index]
      const next = bugTitleLines[index + 1]
      const nextSection = headings.find(
        (heading) => heading.line > current.line && /^\d+[.)]\s/.test(heading.title),
      )
      const end = Math.min(
        next?.line ?? lines.length,
        nextSection?.line ?? lines.length,
      )
      addCandidate(current.title, current.line + 1, end)
    }
    return candidates
  }

  for (let index = 0; index < headings.length; index += 1) {
    const heading = headings[index]
    const title = cleanTitle(heading.title)
    const directBugHeading = /^(?:bug|defect)\s*(?:report\s*)?(?:#?\d+\s*)?[:.)\-–—]/i.test(
      heading.title,
    )
    let enclosingSection: Heading | undefined
    for (let previous = index - 1; previous >= 0; previous -= 1) {
      const candidate = headings[previous]
      if (candidate.level < heading.level) {
        enclosingSection = candidate
        break
      }
    }
    const isInBugSection =
      enclosingSection !== undefined &&
      /\b(?:bugs?|defects?)\b/i.test(enclosingSection.title) &&
      !/^(?:bug|defect)\s*(?:report\s*)?(?:#?\d+\s*)?[:.)\-–—]/i.test(enclosingSection.title) &&
      heading.level > enclosingSection.level
    if (!directBugHeading && !isInBugSection) continue
    if (!directBugHeading && GENERIC_BUG_HEADINGS.test(title)) continue

    let end = lines.length
    for (let next = index + 1; next < headings.length; next += 1) {
      if (headings[next].level <= heading.level) {
        end = headings[next].line
        break
      }
    }
    addCandidate(title, heading.line + 1, end)
  }

  if (candidates.length) return candidates

  const bugSections = headings.flatMap((heading, index) => {
    if (!/\b(?:bugs?|defects?)\b/i.test(heading.title)) return []
    let end = lines.length
    for (let next = index + 1; next < headings.length; next += 1) {
      if (headings[next].level <= heading.level) {
        end = headings[next].line
        break
      }
    }
    return [{ start: heading.line + 1, end }]
  })
  for (const section of bugSections) {
    const sectionLines = lines.slice(section.start, section.end)
    const entries = sectionLines.flatMap((line, index) => {
      const match = /^\s*(?:[-*]|\d+[.)])\s+\*\*(.+?)\*\*\s*:?\s*$/.exec(line)
      return match ? [{ title: match[1], line: index }] : []
    })
    for (let index = 0; index < entries.length; index += 1) {
      const current = entries[index]
      const next = entries[index + 1]
      const body = sectionLines.slice(current.line + 1, next?.line ?? sectionLines.length)
      addCandidate(current.title, 0, 0, body.join('\n'))
    }
    if (entries.length) return candidates
  }

  const labeledTitle = /^\s*(?:[-*]\s*)?\*\*(?:Bug\s+)?(?:Title|Summary)\s*:\*\*\s*(.+?)\s*$/i
  const standaloneTitles = lines.flatMap((line, index) => {
    const labeledMatch = labeledTitle.exec(line)
    if (labeledMatch) return [{ title: labeledMatch[1], line: index }]
    const bugMatch =
      /^\s*(?:[-*]\s*)?\*\*(?:Bug|Defect)\s*(?:Report\s*)?(?:#?\d+\s*)?[:.)-]\s*(.+?)\*\*\s*$/.exec(
        line,
      )
    return bugMatch ? [{ title: bugMatch[1], line: index }] : []
  })
  for (let index = 0; index < standaloneTitles.length; index += 1) {
    const current = standaloneTitles[index]
    const next = standaloneTitles[index + 1]
    addCandidate(
      current.title,
      current.line + 1,
      next?.line ?? lines.length,
    )
  }
  return candidates
}
