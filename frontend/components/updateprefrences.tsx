// PreferenceForm.tsx
import React, { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {Input} from '@/components/ui/Input';
import Toggle from '@/components/ui/Toggle';
import { updatePreference, currentuser} from '@/services/userupdate';
import Field, { inputClass } from "@/components/FormField";

interface PreferenceFormValues {
  currency: string;
  timeZone: string;
  sentOrReceiveDigitalCurrency: boolean;
  receiveMerchantOrder: boolean;
  accountRecommendations: boolean;
}

const PreferenceForm = () => {
  const { control, register, handleSubmit, setValue } = useForm<PreferenceFormValues>({
    defaultValues: {
      currency: 'USD',
      timeZone: 'GMT-5',
      sentOrReceiveDigitalCurrency: false,
      receiveMerchantOrder: false,
      accountRecommendations: false,
    },
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const user = await currentuser();
        const data = user.preferences;
        if (!data) {
          setLoading(false);
          return;
        }

        // Prefill the form with fetched data
        setValue('currency', data.currency || '');
        setValue('timeZone', data.timeZone || '');
        setValue('sentOrReceiveDigitalCurrency', data.sentOrReceiveDigitalCurrency || false);
        setValue('receiveMerchantOrder', data.receiveMerchantOrder || false);
        setValue('accountRecommendations', data.accountRecommendations || false);

        setLoading(false); // Set loading to false after data is fetched
      } catch (error) {
        console.error('Error fetching preferences:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, [setValue]);

  const onSubmit = async (data: PreferenceFormValues) => {
    setSaving(true);
    try {
      await updatePreference(data);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error updating preferences:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p>Loading...</p>; // Optional: Add a loading state

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      {/* Currency and time zone were placeholder-only inputs side by side with no
          labels, and the save button sat under a md:pt-32 gap that left it
          floating far below the form. */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-line dark:bg-surface-1">
        <header className="mb-5">
          <h2 className="text-base font-semibold text-content-primary">Regional</h2>
          <p className="mt-1 text-sm text-content-muted">
            How amounts and times are shown to you.
          </p>
        </header>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field id="currency" label="Currency" hint="For example, USD.">
            <input className={inputClass} {...register('currency')} />
          </Field>
          <Field id="timeZone" label="Time zone" hint="For example, GMT-5.">
            <input className={inputClass} {...register('timeZone')} />
          </Field>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-line dark:bg-surface-1">
        <header className="mb-5">
          <h2 className="text-base font-semibold text-content-primary">Notifications</h2>
          <p className="mt-1 text-sm text-content-muted">
            Choose what BankDash tells you about.
          </p>
        </header>
        <div className="flex flex-col gap-4">
          <Controller
            control={control}
            name="sentOrReceiveDigitalCurrency"
            render={({ field }) => (
              <Toggle label="I send or receive digital currency" {...field} />
            )}
          />
          <Controller
            control={control}
            name="receiveMerchantOrder"
            render={({ field }) => (
              <Toggle label="I receive merchant orders" {...field} />
            )}
          />
          <Controller
            control={control}
            name="accountRecommendations"
            render={({ field }) => (
              <Toggle label="There are recommendations for my account" {...field} />
            )}
          />
        </div>
      </section>

      <div className="flex items-center justify-end gap-4">
        {saved && (
          <p role="status" className="text-sm font-medium text-success">
            Preferences saved
          </p>
        )}
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-brand-fill px-5 py-2.5 text-sm font-medium text-on-brand-fill transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 disabled:opacity-60 dark:focus:ring-offset-dark"
        >
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </form>
  );
};

export default PreferenceForm;
