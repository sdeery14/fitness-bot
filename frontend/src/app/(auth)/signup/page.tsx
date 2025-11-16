import { SignupForm } from "@/components/auth/signup-form";

export default function SignupPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            AI Fitness Planner
          </h1>
          <p className="mt-2 text-gray-600">
            Join thousands achieving their fitness goals with AI
          </p>
        </div>
        <SignupForm />
      </div>
    </div>
  );
}
