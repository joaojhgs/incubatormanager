import type { Metadata } from "next";

import { UserEditClient } from "./UserEditClient";

export const metadata: Metadata = {
  title: "Edit user",
};

export default function StaffUserEditPage({ params }: { params: { id: string } }) {
  return <UserEditClient userId={params.id} />;
}
