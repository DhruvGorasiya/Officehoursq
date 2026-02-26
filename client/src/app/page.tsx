export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg">
      <main className="flex flex-col items-center gap-6 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-card bg-accent/20">
          <span className="text-3xl font-bold text-accent">Q</span>
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-text-primary">
          OfficeHoursQ
        </h1>
        <p className="max-w-md text-lg text-text-secondary">
          Real-time office hours queue management for university courses.
        </p>
        <div className="flex gap-4">
          <a
            href="/login"
            className="rounded-input bg-accent px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-accent-hover"
          >
            Get Started
          </a>
        </div>
      </main>
    </div>
  );
}
