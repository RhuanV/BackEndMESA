/**
 * AssessmentPage — MESA site assessment page.
 *
 * Provides the assessment form within a styled container.
 */
import { AssessmentForm } from '@/features/assessment/components/AssessmentForm';

export function AssessmentPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">
          Avaliação de Sítio — MESA
        </h2>
        <p className="mt-2 text-sm text-neutral-500">
          Preencha os critérios classificatórios conforme o Manual de Apoio 2021
          para avaliação de sítios aeroportuários.
        </p>
      </div>

      <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
        <AssessmentForm />
      </div>
    </div>
  );
}
