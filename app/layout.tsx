import "../styles/globals.css";
import Sidebar from "../components/Sidebar";
import { ReactNode } from "react";

export const metadata = {
  title: "Simple Layout",
  description: "Left menu with empty content area",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="layout">
          <Sidebar />
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
