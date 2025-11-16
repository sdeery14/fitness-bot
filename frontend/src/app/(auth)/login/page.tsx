import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            AI Fitness Planner
          </h1>
          <p className="mt-2 text-gray-600">
            Your personalized path to fitness success
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
