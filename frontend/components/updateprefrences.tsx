// PreferenceForm.tsx
import React, { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {Input} from '@/components/ui/Input';
import Toggle from '@/components/ui/Toggle';
import { updatePreference, currentuser} from '@/services/userupdate';

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
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="md:grid md:grid-cols-2 md:gap-6">
        <div className="md:col-span-2 space-y-4 md:flex md:space-y-0 md:space-x-6">
          <div className="w-full max-w-xs">
            <input
              className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800"
              placeholder="USD"
              {...register('currency')}
            />
          </div>
          <div className="w-full max-w-xs">
            <input
              className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800"
              placeholder="GMT-5"
              {...register('timeZone')}
            />
          </div>
        </div>

        <div className="md:col-span-2 space-y-4">
          <h3 className="font-semibold">Notification</h3>
          <div className="space-y-4 flex flex-col">
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
                <Toggle label="I receive merchant order" {...field} />
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
        </div>
      </div>

      <div className="mt-6 flex justify-center md:pt-32">
        <button
          type="submit"
          disabled={saving}
          className="w-full max-w-xs mx-auto bg-blue-800 text-white py-2 rounded-md disabled:opacity-60"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
        {saved && <p className="text-sm text-green-600 text-center mt-2">Preferences saved</p>}
      </div>
    </form>
  );
};

export default PreferenceForm;
