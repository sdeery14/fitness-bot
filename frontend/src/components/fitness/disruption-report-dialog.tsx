"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { format } from "date-fns";
import { CalendarIcon, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

const disruptionFormSchema = z.object({
  disruptionType: z.enum(["illness", "injury", "travel", "schedule_conflict", "other"], {
    required_error: "Please select a disruption type",
  }),
  severity: z.enum(["minor", "moderate", "severe"], {
    required_error: "Please select severity level",
  }),
  startDate: z.date({
    required_error: "Start date is required",
  }),
  endDate: z.date().optional(),
  description: z.string().min(10, {
    message: "Description must be at least 10 characters",
  }).max(1000, {
    message: "Description must not exceed 1000 characters",
  }),
});

type DisruptionFormValues = z.infer<typeof disruptionFormSchema>;

interface DisruptionReportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  fitnessPlanId: string;
  onDisruptionReported?: (result: any) => void;
}

export function DisruptionReportDialog({
  open,
  onOpenChange,
  fitnessPlanId,
  onDisruptionReported,
}: DisruptionReportDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const form = useForm<DisruptionFormValues>({
    resolver: zodResolver(disruptionFormSchema),
    defaultValues: {
      disruptionType: undefined,
      severity: "moderate",
      startDate: new Date(),
      endDate: undefined,
      description: "",
    },
  });

  async function onSubmit(data: DisruptionFormValues) {
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/v1/ai/reschedule", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fitness_plan_id: fitnessPlanId,
          disruption_type: data.disruptionType,
          severity: data.severity,
          start_date: format(data.startDate, "yyyy-MM-dd"),
          end_date: data.endDate ? format(data.endDate, "yyyy-MM-dd") : null,
          description: data.description,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to report disruption");
      }

      const result = await response.json();

      toast({
        title: "Schedule Rescheduled",
        description: result.data.ai_message || "Your plan has been adjusted for the disruption.",
      });

      onDisruptionReported?.(result.data);
      onOpenChange(false);
      form.reset();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to report disruption",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Report Schedule Disruption</DialogTitle>
          <DialogDescription>
            Let us know about any unexpected events affecting your fitness plan. We'll intelligently
            reschedule your workouts and meals to keep you on track.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="disruptionType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Disruption Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select disruption type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="illness">Illness</SelectItem>
                      <SelectItem value="injury">Injury</SelectItem>
                      <SelectItem value="travel">Travel</SelectItem>
                      <SelectItem value="schedule_conflict">Schedule Conflict</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="severity"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Severity</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select severity" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="minor">Minor (1-2 days impact)</SelectItem>
                      <SelectItem value="moderate">Moderate (3-7 days impact)</SelectItem>
                      <SelectItem value="severe">Severe (7+ days impact)</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    How significantly will this affect your ability to follow the plan?
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="startDate"
                render={({ field }) => (
                  <FormItem className="flex flex-col">
                    <FormLabel>Start Date</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            className={cn(
                              "w-full pl-3 text-left font-normal",
                              !field.value && "text-muted-foreground"
                            )}
                          >
                            {field.value ? (
                              format(field.value, "PPP")
                            ) : (
                              <span>Pick a date</span>
                            )}
                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={field.value}
                          onSelect={field.onChange}
                          disabled={(date) =>
                            date > new Date() || date < new Date("1900-01-01")
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="endDate"
                render={({ field }) => (
                  <FormItem className="flex flex-col">
                    <FormLabel>End Date (Optional)</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            className={cn(
                              "w-full pl-3 text-left font-normal",
                              !field.value && "text-muted-foreground"
                            )}
                          >
                            {field.value ? (
                              format(field.value, "PPP")
                            ) : (
                              <span>Ongoing</span>
                            )}
                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={field.value}
                          onSelect={field.onChange}
                          disabled={(date) =>
                            date < (form.getValues("startDate") || new Date())
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe what happened and how it affects your ability to follow the plan..."
                      className="resize-none"
                      rows={4}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Provide details to help us reschedule appropriately (min 10 characters)
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Report & Reschedule
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
