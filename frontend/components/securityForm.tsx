// SecurityForm.tsx
import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Input } from '@/components/ui/Input';
import Toggle from '@/components/ui/Toggle';
import { changePassword } from '@/services/authentication';

interface SecurityFormValues {
  twoFactorEnabled: boolean;
  currentPassword: string;
  newPassword: string;
}

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
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <h3 className="font-semibold">Two-factor Authentication</h3>
      <Controller
        control={control}
        name="twoFactorEnabled"
        render={({ field }) => (
          <Toggle label="Enable or disable two-factor authentication" {...field} />
        )}
      />

      <h3 className="font-semibold">Change Password</h3>
      <div className="w-full max-w-xs">
        <Input type="password" placeholder="******" {...register('currentPassword')} />
      </div>
      <div className="w-full max-w-xs">
        <Input type="password" placeholder="******" {...register('newPassword')} />
      </div>
      <div className="flex justify-center md:pt-20">
        <button
          type="submit"
          disabled={saving}
          className="w-full max-w-xs mx-auto bg-blue-800 text-white py-2 rounded-md disabled:opacity-60"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
        {message && (
          <p className={`text-sm text-center mt-2 ${message.ok ? 'text-green-600' : 'text-red-500'}`}>
            {message.text}
          </p>
        )}
      </div>
    </form>
  );
};

export default SecurityForm;
