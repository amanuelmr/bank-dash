// SecurityForm.tsx
import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Input } from '@/components/ui/Input';
import Toggle from '@/components/ui/Toggle';
import { changePassword } from '@/services/authentication';
import Field from '@/components/FormField';

interface SecurityFormValues {
  twoFactorEnabled: boolean;
  currentPassword: string;
  newPassword: string;
}

const Section: React.FC<{ title: string; description?: string; children: React.ReactNode }> = ({
  title,
  description,
  children,
}) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-line dark:bg-surface-1">
    <header className="mb-5">
      <h2 className="text-base font-semibold text-content-primary">{title}</h2>
      {description && <p className="mt-1 text-sm text-content-muted">{description}</p>}
    </header>
    {children}
  </section>
);

const SecurityForm = () => {
  const { control, register, handleSubmit } = useForm<SecurityFormValues>({
    defaultValues: { twoFactorEnabled: false, currentPassword: '', newPassword: '' },
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

  const onSubmit = async (data: SecurityFormValues) => {
    setSaving(true);
    setMessage(null);
    try {
      await changePassword(data);
      setMessage({ text: 'Password updated', ok: true });
    } catch (error) {
      setMessage({
        text: error instanceof Error ? error.message : 'Could not update password',
        ok: false,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      <Section
        title="Two-factor authentication"
        description="Require a second step when signing in."
      >
        <Controller
          control={control}
          name="twoFactorEnabled"
          render={({ field }) => (
            <Toggle label="Enable two-factor authentication" {...field} />
          )}
        />
      </Section>

      {/* Both fields were placeholders-only, so once a password was typed there
          was no way to tell the current one from the new one. */}
      <Section title="Change password">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field id="currentPassword" label="Current password">
            <Input type="password" autoComplete="current-password" {...register('currentPassword')} />
          </Field>
          <Field
            id="newPassword"
            label="New password"
            hint="Choose something you have not used before."
          >
            <Input type="password" autoComplete="new-password" {...register('newPassword')} />
          </Field>
        </div>

        <div className="mt-6 flex items-center justify-end gap-4">
          {message && (
            <p
              role="status"
              className={`text-sm font-medium ${message.ok ? 'text-success' : 'text-danger'}`}
            >
              {message.text}
            </p>
          )}
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-brand-fill px-5 py-2.5 text-sm font-medium text-on-brand-fill transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 disabled:opacity-60 dark:focus:ring-offset-surface-1"
          >
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </Section>
    </form>
  );
};

export default SecurityForm;
