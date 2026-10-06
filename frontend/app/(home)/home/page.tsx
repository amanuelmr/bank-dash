"use client";
import React from "react";
import Image from "next/image";
import Link from "next/link";
// Served from public/, so reference by URL. Importing these as modules both
// broke the path alias and bundled ~2MB of PNGs into the client bundle.
const MOBILE_IMAGE = "/Images/landingpageImge.png";

const Landing: React.FC = () => {
  return (
    <>
      {/* From xl up the page is pinned to the viewport so it never scrolls, and
          the hero absorbs whatever height is left over. Below xl nothing changes
          and the page scrolls as it always did - squeezing a phone screen to fit
          would be worse than letting it scroll.

          The threshold is deliberately xl rather than lg: a 1024x768 window does
          not have the height for this, and pinning it there would clip content
          rather than fit it. */}
      <div className="flex flex-col w-full min-h-screen xl:h-screen xl:overflow-hidden dark:bg-dark dark:text-white bg-gray-300 items-center justify-center text-gray-80">
        <div className="p-4 w-[90%] flex flex-col xl:flex-1 xl:min-h-0">
          <div className="flex items-center justify-between shrink-0">
            <div className="flex items-center">
              <Image src='/icons/logo.svg' alt="Logo" width={36} height={36} />
              <div className="text-[#343C6A] dark:text-gray-200 pl-2 md:text-xl md:pl-1 lg:pl-2 lg:text-2xl text-base xl:text-4xl md:text-[21px] font-[800] font-mont">
                BankDash.
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="./signin"
                className="text-lg border text-white bg-indigo-500 border-[#343C6A] hover:bg-indigo-600 hover:text-white px-4 py-2 rounded-3xl text-center w-32"
              >
                Login
              </Link>
              <Link
                href="./signup"
                className="w-32 text-lg border border-indigo-500  hover:bg-indigo-600 text-indigo-600 px-4 py-2 rounded-3xl text-center hover:text-white "
              >
                SignUp
              </Link>
            </div>
          </div>

          {/* items-center is what closes the dead gap: the copy column is far
              shorter than the image, and centring them against each other keeps
              the leftover space split evenly instead of pooling under the
              button. min-h-0 lets this actually shrink instead of overflowing. */}
          <div className="flex flex-col-reverse md:flex-row xl:flex-1 xl:min-h-0 xl:my-[2vh] w-full items-center">
            <div className="w-full md:w-2/5">
              {/* clamp() ties the headline to the viewport height, so a short
                  window gets a smaller headline rather than pushing the feature
                  cards off the bottom. 5rem stops it ballooning on a tall
                  display, where the extra room is better spent on the artwork. */}
              <div className="font-bold text-7xl xl:text-[clamp(2.5rem,7vh,5rem)] py-6 xl:py-2">
                Easy way to manage your money
              </div>
              <div className="py-6 xl:py-3 w-3/4 xl:w-[85%]">
                A new way to make the payments easy reliable and secure. You can
                manage all your transactions from your mobile phone.
              </div>
              <Link
                href="./signup"
                className="text-lg border hover:border-indigo-600 bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-3xl text-center hover:text-black"
              >
                Get Started
              </Link>
            </div>

            <div className="w-full md:w-3/5 flex items-center justify-center">
              {/* max-h stops the 1:1 artwork setting the height of the hero.
                  object-contain letterboxes it rather than cropping. */}
              <Image
                src={MOBILE_IMAGE}
                width={200}
                height={200}
                alt="sample moble of project"
                className="w-full md:w-3/5 xl:max-h-[46vh] object-contain"
              />
            </div>
          </div>
        </div>

        {/* shrink-0 so the cards keep their size and the hero yields the space
            instead. */}
        <div className="relative   md:w-full xl:mt-[1vh] shrink-0 flex flex-col justify-center items-center  p-6 xl:pt-[3vh]">
          <div className="md:w-4/5 z-50 flex flex-wrap  justify-between items-center gap-5">
            {/* min-h rather than a fixed h-24: at this width the longer lines
                wrap to two lines and were being clipped. */}
            <div className="w-[45%] rounded-lg md:w-1/5 flex flex-col items-center justify-center text-center gap-1 dark:bg-gray-600 dark:text-white bg-white shadow-xl hover:scale-105 min-h-[6rem] px-2 py-3">
              <div className="font-bold text-2xl">100% Safe</div>
              <div className="">Your money is safe</div>
            </div>
            <div className="w-[45%] rounded-lg md:w-1/5 flex flex-col items-center justify-center text-center gap-1 dark:bg-gray-600 dark:text-white bg-white shadow-xl hover:scale-105 min-h-[6rem] px-2 py-3">
              <div className="font-bold text-2xl">Quick Send</div>
              <div className="">Transfer money in 1 click</div>
            </div>
            <div className="w-[45%] rounded-lg md:w-1/5 flex flex-col items-center justify-center text-center gap-1 dark:bg-gray-600 dark:text-white bg-white shadow-xl hover:scale-105 min-h-[6rem] px-2 py-3">
              <div className="font-bold text-2xl">Loan</div>
              <div className="">
                Manage your loans efficiently
              </div>
            </div>
            <div className="w-[45%] rounded-lg md:w-1/5 flex flex-col items-center justify-center text-center gap-1 dark:bg-gray-600 dark:text-white bg-white shadow-xl hover:scale-105 min-h-[6rem] px-2 py-3">
              <div className="font-bold text-2xl">Investment</div>
              <div className="">
                Grow your wealth with smart investments
              </div>
            </div>
          </div>
          <div className="absolute -z-0 h-24 md:w-full xl:mt-[1vh]  dark:bg-gray-400 bg-gray-200 flex flex-col justify-center items-center dark:bg-darkComponent md:rounded-t-full rounded-t-3xl p-6 pt-12"></div>
        </div>
      </div>
    </>
  );
};

export default Landing;