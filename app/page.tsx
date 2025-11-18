import { redirect } from "next/navigation";

export default function Page() {
  redirect("/testpage"); // immediately redirects to /testpage

  return "";
}
