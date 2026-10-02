import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import Image from "next/image";
import { updateUserDetails, currentuser } from "@/services/userupdate";
import { FaPencilAlt } from "react-icons/fa";

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
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-6 md:grid md:grid-cols-3 md:gap-2"
    >
      {/* Profile picture section */}
      <div className="flex justify-center md:justify-start md:col-span-1">
        <div className="relative ml-4 h-[160px]">
          <Image
            src={profileImage}
            alt="Profile"
            width={150}
            height={150}
            className="rounded-full aspect-square object-cover"
          />
          {/* Pencil icon for changing profile picture */}
          <span className="absolute bottom-2 right-2 w-10 h-10 p-2 bg-blue-800 rounded-full cursor-pointer flex justify-center items-center">
            <FaPencilAlt
              className="text-white"
              onClick={() => document.getElementById("fileInput")?.click()}
            />
            <input
              id="fileInput"
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden" // Hidden file input
            />
          </span>
        </div>
      </div>

      {/* Form fields */}
      <div className="md:col-span-1 space-y-4">
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            placeholder="John Doe"
            {...register("name", { required: true })}
          />
          {errors.name && <p className="text-red-500">Name is required</p>}
        </div>
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            type="email"
            placeholder="john@example.com"
            {...register("email", { required: true })}
          />
          {errors.email && <p className="text-red-500">Email is required</p>}
        </div>
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            type="date"
            {...register("dateOfBirth")}
          />
        </div>
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            placeholder="123 Main St"
            {...register("permanentAddress")}
          />
        </div>
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            placeholder="12345"
            {...register("postalCode")}
          />
        </div>
      </div>

      <div className="md:col-span-1 space-y-4">
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            placeholder="john_doe"
            {...register("username", { required: true })}
          />
          {errors.username && (
            <p className="text-red-500">Username is required</p>
          )}
        </div>
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            placeholder="456 Another St"
            {...register("presentAddress")}
          />
        </div>
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            placeholder="City"
            {...register("city")}
          />
        </div>
        <div className="w-full max-w-xs mx-auto sm:w-11/12 sm:mx-0 md:w-full">
          <input
            className="mt-1 p-2 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-800 w-full"
            placeholder="Country"
            {...register("country")}
          />
        </div>
      </div>

      {/* Submit button */}
      <div className="md:col-span-3 flex justify-end">
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-blue-800 text-white rounded-lg hover:bg-blue-700 focus:outline-none disabled:opacity-60"
        >
          {saving ? 'Saving…' : 'Save Changes'}
        </button>
        {saved && <p className="text-sm text-green-600">Profile updated</p>}
      </div>
    </form>
  );
};

export default EditProfileForm;
