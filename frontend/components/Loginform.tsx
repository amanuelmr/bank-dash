"use client";
import React, { useState } from "react";
import { useForm } from "react-hook-form";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  AtSymbolIcon,
  KeyIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  
} from "@heroicons/react/24/outline";
import { creditcardstyles, colors ,logo } from "../constants/index";
import { ApiError } from '@/lib/apiClient';
import { loginUser } from '@/services/authentication';

interface LoginFormValues {
  username: string;
  password: string;
}


const LoginForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>();

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const router = useRouter()

  const onSubmit = async ({ username, password }: LoginFormValues) => {
    setIsLoading(true);
    setErrorMessage("");
    try {
      // loginUser stores the tokens, so every later request is authenticated.
      await loginUser(username, password);

      setIsLoading(false);
      router.push("/");
      router.refresh();
    } catch (error) {
      setIsLoading(false);
      if (error instanceof ApiError) {
        setErrorMessage(error.message || "Login failed. Please try again.");
      } else if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("An unexpected error occurred.");
      }
    }
  };

  return (
    <div className="flex items-center justify-center max-h-screen py-4 overflow-hidden">
      <div className="flex-col items-center justify-center w-[50vh]">
      <form onSubmit={handleSubmit(onSubmit)} className="p-4 rounded-2xl">
      <div className="flex items-center">
              <Image src='/icons/logo.svg' alt="Logo" width={36} height={36} />
              <div className="text-[#343C6A] dark:text-gray-200 pl-2 md:text-xl md:pl-1 lg:pl-2 lg:text-2xl text-base xl:text-4xl md:text-[21px] font-[800] font-mont">
                BankDash.
              </div>
            </div> 

        <div className="py-4">
        <div>
          <label htmlFor="username" className="block font-bold mb-2 text-gray-700 dark:text-white">
          UserName
          </label>
          <input
          id="username"
          type="text"
          placeholder="Username"  
          defaultValue="tester"
          {...register("username", { required: "Username is required" })}
          className="w-full m-auto border-gray-200  dark:text-dark dark:bg-surface-1 border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
          />
          {errors.username && (
          <div className="flex gap-1">
            <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
            <p className="text-red-500">{errors.username.message as string}</p>
          </div>
          )}
        </div>
        </div>

        <div className="py-4">
        <div>
          <label htmlFor="password" className="block font-bold mb-2 text-gray-700 dark:text-white">
          Password
          </label>
          <input
          id="password"
          type="password"
          placeholder="Password"
          defaultValue={"12345678"}
          {...register("password", { required: "Password is required" })}
          className="w-full m-auto border-gray-200 dark:text-dark dark:bg-surface-1 border-2 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-10 px-2.5"
          />
          {errors.password && (
          <div className="flex gap-1">
            <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
            <p className="text-red-500">{errors.password.message as string}</p>
          </div>
          )}
        </div>
        </div>

        {errorMessage && (
        <div className="text-red-500 text-center mb-4">
          {errorMessage} Enter valid credentials
        </div>
        )}

        <div className="flex items-center justify-center">
        <button
        type="submit"
        className={` text-white px-4 py-2 mt-4 w-full rounded-3xl text-xl hover:bg-indigo-600 ${isLoading ? 'bg-indigo-500 cursor-not-allowed hover:bg-indigo-500' : 'bg-indigo-700' }`}
        >
        {isLoading ? (

          <div className="flex justify-center items-center ">
            <ArrowPathIcon className="h-5 w-5 animate-spin  text-white  " />
          </div>
        ) : (
          
          "Login"
        )}
        </button>
        
        </div>

        <div className="my-14 flex flex-col items-center text-l ">
        <p className={`${colors.textgray}`}>
          Don&apos;t have an account?{" "}
          <span className={`${colors.textblue} font-medium text-l`}>
          <Link href="./signup" className="dark:text-content-primary" >Sign Up</Link>
          </span>
        </p>
        <span className={`${colors.textblue} dark:text-content-primary font-medium text-l py-2`}>
          <Link href="/forgotpassword">Forgot password?</Link>
        </span>
        </div>
      </form>
      </div>
    </div>
    );
};

export default LoginForm;
