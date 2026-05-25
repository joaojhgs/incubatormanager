import type { Metadata } from "next";

import { tUsers } from "@/lib/i18n/users";

import { UserEditClient } from "./UserEditClient";

export const metadata: Metadata = {
  title: tUsers("editTitle"),
};

export default function StaffUserEditPage({ params }: { params: { id: string } }) {
  return <UserEditClient userId={params.id} />;
}
