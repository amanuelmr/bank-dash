'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useForm, SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import Link from 'next/link'
import Image from 'next/image'
import { ArrowPathIcon, ExclamationCircleIcon } from "@heroicons/react/24/outline"
import { Switch } from '@/components/ui/switch'

const formSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters." }),
  email: z.string().email({ message: "Invalid email address." }),
  dateOfBirth: z.string().refine((date) => new Date(date) <= new Date(), { message: "Date of birth cannot be in the future." }),
  username: z.string().min(3, { message: "Username must be at least 3 characters." }),
  password: z.string().min(8, { message: "Password must be at least 8 characters." }),
  permanentAddress: z.string().min(1, { message: "Permanent address is required." }),
  presentAddress: z.string().min(1, { message: "Present address is required." }),
  postalCode: z.string().min(1, { message: "Postal code is required." }),
  city: z.string().min(1, { message: "City is required." }),
  country: z.string().min(1, { message: "Country is required." }),
  profilePicture: z.string().optional(),
  preference: z.object({
    currency: z.string().min(1, { message: "Currency is required." }),
    timeZone: z.string().min(1, { message: "Time zone is required." }),
    sentOrReceiveDigitalCurrency: z.boolean(),
    receiveMerchantOrder: z.boolean(),
    accountRecommendations: z.boolean(),
    twoFactorAuthentication: z.boolean()
  })
})

type FormValues = z.infer<typeof formSchema>

export default function SignupForm() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [showErrors, setShowErrors] = useState(false)

  const { register, handleSubmit, formState: { errors }, trigger, setValue, watch } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      profilePicture: "",
      preference: {
        currency: "",
        timeZone: "",
        sentOrReceiveDigitalCurrency: false,
        receiveMerchantOrder: false,
        accountRecommendations: false,
        twoFactorAuthentication: false
      }
    }
  })

  const onSubmit: SubmitHandler<FormValues> = async (data) => {
    setShowErrors(true)
    const isValid = await trigger()
    if (isValid) {
      setIsLoading(true)
      setErrorMessage("")
      try {
        console.log("Submitting data:", data)
        const response = await fetch('https://bank-dash-36iy.onrender.com/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        })
        if (response.ok) {
          router.push('/signin')
        } else {
          const errorData = await response.json()
          setErrorMessage(errorData.message || "Signup failed. Please try again.")
        }
      } catch (error) {
        console.error('Error during signup:', error)
        setErrorMessage("An unexpected error occurred.")
      } finally {
        setIsLoading(false)
      }
    }
  }

  const nextStep = async () => {
    const fieldsToValidate = {
      1: ["name", "email", "username", "password", "dateOfBirth"],
      2: ["permanentAddress", "presentAddress", "postalCode", "city", "country"],
      3: ["preference.currency", "preference.timeZone"]
    }[step] as (keyof FormValues)[];

    setShowErrors(true)
    const isValid = await trigger(fieldsToValidate);
    if (isValid) {
      setStep(prev => Math.min(prev + 1, 3));
      setShowErrors(false)
    }
  }

  const prevStep = () => {
    setStep(prev => Math.max(prev - 1, 1))
    setShowErrors(false)
  }

  const handleSwitchChange = (field: keyof FormValues['preference']) => {
    setValue(`preference.${field}`, !watch(`preference.${field}`))
  }

  useEffect(() => {
    const subscription = watch((value, { name, type }) => {
      if (type === 'change' && errors[name as keyof FormValues]) {
        trigger(name as keyof FormValues);
      }
    });
    return () => subscription.unsubscribe();
  }, [watch, errors, trigger]);

  const showError = (fieldName: string) => {
    return showErrors && errors[fieldName as keyof FormValues];
  }

  return (
    <div className="flex items-center justify-center max-h-screen py-2 overflow-hidden">
      <div className="flex-col items-center justify-center w-[50vh]">
        <form onSubmit={handleSubmit(onSubmit)} className="p-2 rounded-2xl">
          <div className="flex items-center">
            <Image src='/icons/logo.svg' alt="Logo" width={36} height={36} />
            <div className="text-[#343C6A] dark:text-gray-200 pl-2 md:text-xl md:pl-1 lg:pl-2 lg:text-2xl text-base xl:text-4xl md:text-[21px] font-[800] font-mont">
              BankDash.
            </div>
          </div>  

          {step === 1 && (
            <>
              <div className="py-2">
                <label htmlFor="name" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Full Name
                </label>
                <input
                  id="name"
                  type="text"
                  placeholder="Full Name"
                  {...register("name")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("name") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.name?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="email" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="Email"
                  {...register("email")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("email") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.email?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="dateOfBirth" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Date of Birth
                </label>
                <input
                  id="dateOfBirth"
                  type="date"
                  {...register("dateOfBirth")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("dateOfBirth") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.dateOfBirth?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="username" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  placeholder="Username"
                  {...register("username")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("username") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.username?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="password" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  placeholder="Password"
                  {...register("password")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("password") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.password?.message}</p>
                  </div>
                )}
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div className="py-2">
                <label htmlFor="permanentAddress" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Permanent Address
                </label>
                <input
                  id="permanentAddress"
                  type="text"
                  placeholder="Permanent Address"
                  {...register("permanentAddress")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("permanentAddress") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.permanentAddress?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="presentAddress" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Present Address
                </label>
                <input
                  id="presentAddress"
                  type="text"
                  placeholder="Present Address"
                  {...register("presentAddress")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("presentAddress") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.presentAddress?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="postalCode" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Postal Code
                </label>
                <input
                  id="postalCode"
                  type="text"
                  placeholder="Postal Code"
                  {...register("postalCode")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("postalCode") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.postalCode?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="city" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  City
                </label>
                <input
                  id="city"
                  type="text"
                  placeholder="City"
                  {...register("city")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("city") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.city?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="country" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Country
                </label>
                <input
                  id="country"
                  type="text"
                  placeholder="Country"
                  {...register("country")}
                  className="w-full  m-auto border-gray-200  dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                />
                {showError("country") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.country?.message}</p>
                  </div>
                )}
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <div className="py-2">
                <label htmlFor="currency" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Preferred Currency
                </label>
                <select
                  id="currency"
                  {...register("preference.currency")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                >
                  <option value="">Select currency</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
                {showError("preference.currency") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.preference?.currency?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2">
                <label htmlFor="timeZone" className="block font-bold mb-2 text-gray-700 dark:text-white">
                  Time Zone
                </label>
                <select
                  id="timeZone"
                  {...register("preference.timeZone")}
                  className="w-full m-auto border-gray-200 dark:text-dark dark:bg-white border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
                >
                  <option value="">Select time zone</option>
                  <option value="UTC">UTC</option>
                  <option value="EST">EST</option>
                  <option value="PST">PST</option>
                </select>
                {showError("preference.timeZone") && (
                  <div className="flex gap-1">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                    <p className="text-red-500">{errors.preference?.timeZone?.message}</p>
                  </div>
                )}
              </div>

              <div className="py-2 space-y-4">
                <div className="flex items-center justify-between">
                  <label htmlFor="sentOrReceiveDigitalCurrency" className="font-medium text-gray-700 dark:text-white">
                    Send or Receive Digital Currency
                  </label>
                  <Switch
                    id="sentOrReceiveDigitalCurrency"
                    checked={watch("preference.sentOrReceiveDigitalCurrency")}
                    onCheckedChange={() => handleSwitchChange("sentOrReceiveDigitalCurrency")}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <label htmlFor="receiveMerchantOrder" className="font-medium text-gray-700 dark:text-white">
                    Receive Merchant Order
                  </label>
                  <Switch
                    id="receiveMerchantOrder"
                    checked={watch("preference.receiveMerchantOrder")}
                    onCheckedChange={() => handleSwitchChange("receiveMerchantOrder")}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <label htmlFor="accountRecommendations" className="font-medium text-gray-700 dark:text-white">
                    Account Recommendations
                  </label>
                  <Switch
                    id="accountRecommendations"
                    checked={watch("preference.accountRecommendations")}
                    onCheckedChange={() => handleSwitchChange("accountRecommendations")}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <label htmlFor="twoFactorAuthentication" className="font-medium text-gray-700 dark:text-white">
                    Two-Factor Authentication
                  </label>
                  <Switch
                    id="twoFactorAuthentication"
                    checked={watch("preference.twoFactorAuthentication")}
                    onCheckedChange={() => handleSwitchChange("twoFactorAuthentication")}
                  />
                </div>
              </div>
            </>
          )}

          {errorMessage && (
            <div className="text-red-500 text-center mb-4">
              {errorMessage}
            </div>
          )}

          <div className="flex items-center justify-between gap-4">
            {step > 1 && (
              <button
                onClick={prevStep}
                className="text-indigo-600 px-4 py-2 mt-4 w-40 rounded-3xl text-xl border border-indigo-600 hover:bg-indigo-500 hover:text-white"
              >
                Previous
              </button>
            )}
            {step < 3 ? (
              <button
                onClick={nextStep}
                className="bg-indigo-600 text-white px-4 py-2 mt-4 w-32 rounded-3xl text-xl hover:bg-indigo-700 h-10"
              >
                Next
              </button>
            ) : (
              <button
                type="submit"
                className={`bg-indigo-600 text-white px-4 py-2 mt-4 w-40 rounded-3xl text-xl hover:bg-indigo-700 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="flex justify-center items-center">
                    <ArrowPathIcon className="h-5 w-5 animate-spin text-white" />
                  </div>
                ) : (
                  "Sign Up"
                )}
              </button>
            )}
          </div>

          {step === 1 && (
            <div className="my-14 flex flex-col items-center text-l">
              <p className="text-gray-600 dark:text-gray-300">
                Already have an account?{" "}
                <span className="text-indigo-600 font-medium text-l">
                  <Link href="./login" className="dark:text-gray-300">Login</Link>
                </span>
              </p>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}