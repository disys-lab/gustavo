"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useQuery } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { getMyGroups } from "@/lib/api/users";
import { useAuth } from "@/lib/context/AuthContext";

const schema = z.object({
  name: z.string().min(1, "Name required").regex(/^[a-z0-9_-]+$/, "Lowercase letters, numbers, dashes, underscores"),
  owner_group: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

interface DeviceGroupFormProps {
  defaultValues?: Partial<FormValues>;
  onSubmit: (values: FormValues) => Promise<void>;
  isEdit?: boolean;
}

export function DeviceGroupForm({ defaultValues, onSubmit, isEdit = false }: DeviceGroupFormProps) {
  const { isAdmin } = useAuth();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", owner_group: "", ...defaultValues },
  });

  const { data: myGroupsData } = useQuery({
    queryKey: ["my-groups"],
    queryFn: getMyGroups,
    enabled: !isEdit && !isAdmin,
    staleTime: 30_000,
  });
  const myGroups: string[] = !myGroupsData?.error ? myGroupsData?.response.groups ?? [] : [];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-sm">
      <div>
        <Label htmlFor="dg-name">Device Group Name</Label>
        <Input id="dg-name" {...register("name")} disabled={isEdit} className="mt-1" />
        {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>}
      </div>

      {!isEdit && !isAdmin && (
        myGroups.length === 0 ? (
          <p className="text-sm text-red-600">
            You&apos;re not a member of any group yet — ask an admin to add you to one before creating device groups.
          </p>
        ) : myGroups.length === 1 ? (
          <p className="text-sm text-muted-foreground">
            This device group will be owned by your group <strong>{myGroups[0]}</strong>.
          </p>
        ) : (
          <div>
            <Label htmlFor="dg-owner-group">Which group should own this device group?</Label>
            <select
              id="dg-owner-group"
              {...register("owner_group")}
              className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
            >
              <option value="">Select a group…</option>
              {myGroups.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>
        )
      )}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : isEdit ? "Update" : "Create Device Group"}
      </Button>
    </form>
  );
}
