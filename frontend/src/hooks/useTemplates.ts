import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";

export const templateKeys = {
  all: ["templates"] as const,
  lists: () => [...templateKeys.all, "list"] as const,
  list: () => [...templateKeys.lists()] as const,
  active: () => [...templateKeys.all, "active"] as const,
  impactAnalysis: () => [...templateKeys.all, "impact-analysis"] as const,
};

export function useTemplates() {
  return useQuery({
    queryKey: templateKeys.list(),
    queryFn: () => api.getTemplates(),
  });
}

export function useActiveTemplate() {
  return useQuery({
    queryKey: templateKeys.active(),
    queryFn: () => api.getActiveTemplate(),
  });
}

export function useTemplateImpactAnalysis() {
  return useQuery({
    queryKey: templateKeys.impactAnalysis(),
    queryFn: () => api.getTemplateImpactAnalysis(),
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { version: string; template_schema: unknown }) =>
      api.createTemplate(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: templateKeys.all });
    },
  });
}

export function useUploadTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { version: string; file: File }) =>
      api.uploadTemplate(variables.version, variables.file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: templateKeys.all });
    },
  });
}

export function useAnalyzeTemplate() {
  return useMutation({
    mutationFn: (variables: { version: string; file: File }) =>
      api.analyzeTemplate(variables.version, variables.file),
  });
}
