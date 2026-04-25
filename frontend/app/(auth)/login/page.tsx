import { Spin } from "antd";
import { Suspense } from "react";

import LoginForm from "./LoginForm";

export default function LoginPage() {
  return (
    <Suspense fallback={<Spin size="large" style={{ margin: "48px auto", display: "block" }} />}>
      <LoginForm />
    </Suspense>
  );
}
