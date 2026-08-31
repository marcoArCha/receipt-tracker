import { CognitoUserPool } from "amazon-cognito-identity-js";

const poolData = {
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
};

if (!poolData.UserPoolId || !poolData.ClientId) {
  console.error(
    "Missing Cognito config. Check that VITE_COGNITO_USER_POOL_ID and " +
      "VITE_COGNITO_CLIENT_ID are set in your .env file."
  );
}

export const userPool = new CognitoUserPool(poolData);
