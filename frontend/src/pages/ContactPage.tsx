import './ContactPage.css'

const CONTACT_EMAIL = 'monika.tyagi@alight.com'

export function ContactPage() {
  return (
    <div className="contact-page">
      <header className="contact-hero">
        <p className="eyebrow">Contact</p>
        <h1>We’re here to help</h1>
        <p>
          Have a question, feedback, or need help using Quality Assistance? Contact the project
          owner using the details below.
        </p>
      </header>

      <section className="contact-card panel" aria-labelledby="contact-card-title">
        <div className="contact-avatar" aria-hidden="true">MT</div>
        <div className="contact-details">
          <h2 id="contact-card-title">Monika Tyagi</h2>
          <p className="contact-role">Quality Assistance application contact</p>
          <a className="contact-email" href={`mailto:${CONTACT_EMAIL}`}>
            {CONTACT_EMAIL}
          </a>
          <a
            className="btn btn-primary contact-button"
            href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent('Quality Assistance app inquiry')}`}
          >
            Email Monika
          </a>
        </div>
      </section>

      <p className="contact-note">
        When reporting an issue, include what you were trying to do and any non-sensitive error
        message. Please do not email passwords, access tokens, customer data, or other secrets.
      </p>
    </div>
  )
}
