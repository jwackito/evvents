import { create } from "zustand";
import type { Organization } from "@/types";

interface OrgState {
  currentOrg: Organization | null;
  setOrg: (org: Organization | null) => void;
}

export const useOrgStore = create<OrgState>((set) => ({
  currentOrg: null,
  setOrg: (org) => set({ currentOrg: org }),
}));
