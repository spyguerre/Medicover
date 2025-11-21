import "../styles/globals.css";
import Sidebar from "../components/Sidebar";
import { ReactNode } from "react";

export const metadata = {
  title: "Medicover",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="layout">
          <main className="content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
