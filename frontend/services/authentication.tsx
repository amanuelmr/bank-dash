import axios from 'axios';

interface UserData {
  name: string;
  email: string;
  dateOfBirth: string;
  permanentAddress: string;
  postalCode: string;
  username: string;
  password: string;
  presentAddress: string;
  city: string;
  country: string;
  profilePicture?: string;
  currency: string;
  preference: {
    sentOrReceiveDigitalCurrency: boolean;
    receiveMerchantOrder: boolean;
    accountRecommendations: boolean;
    timeZone: string;
    twoFactorAuthentication: boolean;
  };
}

export const registerUser = async (userData: UserData) => {
  try {
    // Format the userData to match the expected request body
    const formattedData = {
      name: userData.name,
      email: userData.email,
      dateOfBirth: new Date(userData.dateOfBirth).toISOString(),
      permanentAddress: userData.permanentAddress,
      postalCode: userData.postalCode,
      username: userData.username,
      password: userData.password,
      presentAddress: userData.presentAddress,
      city: userData.city,
      country: userData.country,
      profilePicture: userData.profilePicture || "",
      preference: {
        currency: userData.currency,
        sentOrReceiveDigitalCurrency: userData.preference.sentOrReceiveDigitalCurrency,
        receiveMerchantOrder: userData.preference.receiveMerchantOrder,
        accountRecommendations: userData.preference.accountRecommendations,
        timeZone: userData.preference.timeZone,
        twoFactorAuthentication: userData.preference.twoFactorAuthentication
      }
    };

    const response = await axios.post(
      "https://bank-dash-36iy.onrender.com/auth/register",
      formattedData,
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.log('Error from here', )
      console.error("Axios Error:", error.response?.data || error.message);
      throw new Error(error.response?.data?.message || "Failed to register user");
    } else {
      console.error("Unexpected Error:", error);
      throw new Error("An unexpected error occurred");
    }
  }
};

// Refresh Token - POST Request
export const refreshToken = async (tokenData: any) => {
  try {
    const response = await fetch(
      "https://bank-dash-36iy.onrender.com/auth/refresh_token",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(tokenData),
      }
    );

    if (!response.ok) {
      throw new Error("Failed to refresh token");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    throw error;
  }
};

// Login User - POST Request
export const loginUser = async (loginData: any) => {
  try {
    const response = await fetch("https://bank-dash-36iy.onrender.com/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(loginData),
    });

    if (!response.ok) {
      throw new Error("Failed to login");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    throw error;
  }
};

// Change Password - POST Request
export const changePassword = async (passwordData: any) => {
  try {
    const response = await fetch(
      "https://bank-dash-36iy.onrender.com/auth/change_password",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(passwordData),
      }
    );

    if (!response.ok) {
      throw new Error("Failed to change password");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    throw error;
  }
};

// You can export all functions from this file
