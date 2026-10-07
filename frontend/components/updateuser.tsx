import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import Image from "next/image";
import { updateUserDetails, currentuser } from "@/services/userupdate";
import { FaPencilAlt } from "react-icons/fa";
import Field, { inputClass } from "@/components/FormField";

interface EditProfileFormData {
  name: string;
  email: string;
  dateOfBirth: string;
  permanentAddress: string;
  postalCode: string;
  username: string;
  presentAddress: string;
  city: string;
  country: string;
  profilePicture: string; // URL
}

const Section: React.FC<{
  title: string;
  description?: string;
  children: React.ReactNode;
}> = ({ title, description, children }) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-line dark:bg-surface-1">
    <header className="mb-5">
      <h2 className="text-base font-semibold text-content-primary">{title}</h2>
      {description && (
        <p className="mt-1 text-sm text-content-muted">{description}</p>
      )}
    </header>
    {children}
  </section>
);

const EditProfileForm = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<EditProfileFormData>();

  const [profileImage, setProfileImage] = useState<string>("/Images/profilepic.jpeg");
  const [file, setFile] = useState<File | null>(null); // kept for the file picker preview
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Fetch user data and prefill form
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const userData = await currentuser();

        // Prefill the form with the fetched data
        setValue("name", userData.name);
        setValue("email", userData.email);
        setValue("dateOfBirth", userData.dateOfBirth);
        setValue("permanentAddress", userData.permanentAddress);
        setValue("postalCode", userData.postalCode);
        setValue("username", userData.username);
        setValue("presentAddress", userData.presentAddress);
        setValue("city", userData.city);
        setValue("country", userData.country);
      } catch (error) {
        console.error("Error fetching user data:", error);
      }
    };

    fetchUserData();
  }, [setValue]);

  // Preview the chosen image locally; the file itself is not uploaded anywhere.
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setProfileImage(URL.createObjectURL(selectedFile));
  };

  const onSubmit = async (data: EditProfileFormData) => {
    setSaving(true);
    try {
      await updateUserDetails({
        ...data,
        dateOfBirth: data.dateOfBirth || undefined,
        profilePicture: profileImage,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Error updating user details:", error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      {/* Identity: the photo and the three fields that describe who the account
          belongs to, rather than the photo sitting alone in a column of its own
          with five unrelated fields stacked beside it. */}
      <Section
        title="Profile"
        description="How you appear in BankDash, and how people reach you."
      >
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
          <div className="flex shrink-0 flex-col items-center gap-2">
            <div className="relative">
              <Image
                src={profileImage}
                alt="Profile"
                width={104}
                height={104}
                className="aspect-square rounded-full object-cover ring-1 ring-slate-200 dark:ring-line"
              />
              <button
                type="button"
                onClick={() => document.getElementById("fileInput")?.click()}
                aria-label="Change profile picture"
                className="absolute bottom-0 right-0 flex h-8 w-8 items-center justify-center rounded-full bg-brand-fill text-white transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 dark:focus:ring-offset-surface-1"
              >
                <FaPencilAlt className="text-xs" aria-hidden />
              </button>
              <input
                id="fileInput"
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
            <p className="text-xs text-content-muted">JPG or PNG</p>
          </div>

          <div className="grid flex-1 gap-4 sm:grid-cols-2">
            <Field
              id="name"
              label="Full name"
              error={errors.name && "Name is required"}
            >
              <input className={inputClass} {...register("name", { required: true })} />
            </Field>

            <Field
              id="username"
              label="Username"
              error={errors.username && "Username is required"}
            >
              <input
                className={inputClass}
                {...register("username", { required: true })}
              />
            </Field>

            <Field
              id="email"
              label="Email address"
              className="sm:col-span-2"
              error={errors.email && "Email is required"}
            >
              <input
                type="email"
                className={inputClass}
                {...register("email", { required: true })}
              />
            </Field>
          </div>
        </div>
      </Section>

      <Section title="Personal">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field id="dateOfBirth" label="Date of birth">
            <input type="date" className={inputClass} {...register("dateOfBirth")} />
          </Field>
        </div>
      </Section>

      {/* Addresses were previously split across two columns by position in the
          form rather than by what they were, so present and permanent address
          ended up in different columns with nothing marking them as a pair. */}
      <Section title="Addresses">
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="flex flex-col gap-4">
            <Field
              id="presentAddress"
              label="Present address"
              hint="Where you live now"
            >
              <input className={inputClass} {...register("presentAddress")} />
            </Field>
            <Field id="city" label="City">
              <input className={inputClass} {...register("city")} />
            </Field>
          </div>

          <div className="flex flex-col gap-4">
            <Field
              id="permanentAddress"
              label="Permanent address"
              hint="Used for official correspondence"
            >
              <input className={inputClass} {...register("permanentAddress")} />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field id="postalCode" label="Postal code">
                <input className={inputClass} {...register("postalCode")} />
              </Field>
              <Field id="country" label="Country">
                <input className={inputClass} {...register("country")} />
              </Field>
            </div>
          </div>
        </div>
      </Section>

      <div className="flex items-center justify-end gap-4">
        {saved && (
          <p
            role="status"
            className="text-sm font-medium text-success"
          >
            Profile updated
          </p>
        )}
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-brand-fill px-5 py-2.5 text-sm font-medium text-on-brand-fill transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 disabled:opacity-60 dark:focus:ring-offset-dark"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
      </div>
    </form>
  );
};

export default EditProfileForm;
