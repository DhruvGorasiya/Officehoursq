export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="rounded-card bg-card border border-surface p-8 max-w-md text-center">
        <h1 className="text-2xl font-semibold text-white mb-2">
          OfficeHoursQ
        </h1>
        <p className="text-gray-400 text-sm">
          Real-time office hours queue for students, TAs, and professors.
        </p>
      </div>
    </main>
  );
}
