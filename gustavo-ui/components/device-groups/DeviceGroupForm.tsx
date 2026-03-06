"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

const schema = z.object({
  name: z.string().min(1, "Name required").regex(/^[a-z0-9_-]+$/, "Lowercase letters, numbers, dashes, underscores"),
});

type FormValues = z.infer<typeof schema>;

interface DeviceGroupFormProps {
  defaultValues?: Partial<FormValues>;
  onSubmit: (values: FormValues) => Promise<void>;
  isEdit?: boolean;
}

export function DeviceGroupForm({ defaultValues, onSubmit, isEdit = false }: DeviceGroupFormProps) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", ...defaultValues },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-sm">
      <div>
        <Label htmlFor="dg-name">Device Group Name</Label>
        <Input id="dg-name" {...register("name")} disabled={isEdit} className="mt-1" />
        {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : isEdit ? "Update" : "Create Device Group"}
      </Button>
    </form>
  );
}
