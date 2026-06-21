import Markdown from 'react-markdown'
import './MarkdownContent.css'

type MarkdownContentProps = {
  content: string
}

export function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <div className="markdown-content">
      <Markdown>{content}</Markdown>
    </div>
  )
}
