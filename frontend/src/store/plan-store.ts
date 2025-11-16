import { create } from "zustand";

interface FitnessPlan {
  id: string;
  goal: string;
  duration_weeks: number;
  status: string;
  created_at: string;
  completed_at?: string;
  requirements: {
    fitness_level?: string;
    equipment_access?: string[];
    dietary_restrictions?: string[];
    workout_frequency?: number;
  };
}

interface PlanState {
  activePlan: FitnessPlan | null;
  plans: FitnessPlan[];
  isLoading: boolean;
  error: string | null;
  setActivePlan: (plan: FitnessPlan | null) => void;
  setPlans: (plans: FitnessPlan[]) => void;
  addPlan: (plan: FitnessPlan) => void;
  updatePlan: (planId: string, updates: Partial<FitnessPlan>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const usePlanStore = create<PlanState>((set) => ({
  activePlan: null,
  plans: [],
  isLoading: false,
  error: null,
  setActivePlan: (plan) =>
    set({
      activePlan: plan,
    }),
  setPlans: (plans) =>
    set({
      plans,
    }),
  addPlan: (plan) =>
    set((state) => ({
      plans: [plan, ...state.plans],
    })),
  updatePlan: (planId, updates) =>
    set((state) => ({
      plans: state.plans.map((plan) =>
        plan.id === planId ? { ...plan, ...updates } : plan
      ),
      activePlan:
        state.activePlan?.id === planId
          ? { ...state.activePlan, ...updates }
          : state.activePlan,
    })),
  setLoading: (loading) =>
    set({
      isLoading: loading,
    }),
  setError: (error) =>
    set({
      error,
    }),
  clearError: () =>
    set({
      error: null,
    }),
}));
