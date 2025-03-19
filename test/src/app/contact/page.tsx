"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function ContactPage() {
  const translations = {
    nl: {
      title: "Contacteer Ons",
      description: "Neem contact op met een van onze teamleden.",
      name: "Naam",
      email: "E-mail",
      message: "Bericht",
      send: "Verstuur",
      home: "Home",
      generate: "Genereer",
      about: "Over",
      contact: "Contact",
      help: "Help",
    },
    en: {
      title: "Contact Us",
      description: "Get in touch with one of our team members.",
      name: "Name",
      email: "Email",
      message: "Message",
      send: "Send",
      home: "Home",
      generate: "Generate",
      about: "About",
      contact: "Contact",
      help: "Help",
    },
  } as const; // Ensures translations are strictly typed

  type Language = keyof typeof translations; // 'nl' | 'en'

  const [language, setLanguage] = useState<Language>("nl"); // Explicitly define type

  return (
    <div className="min-h-screen flex flex-col items-center text-center p-6">
      {/* Navbar */}
      <nav className="w-full flex justify-between items-center p-4 border-b shadow-sm fixed top-0 left-0 bg-white z-50">
        <div className="text-2xl font-bold">[LOGO]</div>
        <div className="space-x-4">
          <Link href="/">
            <Button variant="ghost">{translations[language].home}</Button>
          </Link>
          <Link href="/generate">
            <Button variant="outline" className="bg-blue-200">{translations[language].generate}</Button>
          </Link>
          <Link href="/about">
            <Button variant="ghost">{translations[language].about}</Button>
          </Link>
          <Link href="/contact">
            <Button variant="ghost">{translations[language].contact}</Button>
          </Link>
          <Link href="/help">
            <Button variant="ghost">{translations[language].help}</Button>
          </Link>
          <Button onClick={() => setLanguage(language === "nl" ? "en" : "nl")}>
            {language === "nl" ? "English" : "Nederlands"}
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex flex-col items-center mt-24 max-w-3xl">
        <h1 className="text-4xl font-bold">{translations[language].title}</h1>
        <p className="mt-4 text-gray-600">{translations[language].description}</p>

        {/* Team Members */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {[1, 2, 3, 4].map((member) => (
            <div key={member} className="p-4 border rounded-lg shadow-sm w-80">
              <h2 className="text-xl font-semibold">Naam Lid {member}</h2>
              <p className="text-gray-500">Rol: (bijv. Ontwikkelaar)</p>
              <p className="text-gray-600">Email: example@email.com</p>
              <p className="text-gray-500 mt-2">Korte beschrijving van dit lid.</p>
            </div>
          ))}
        </div>

        {/* Contact Form */}
        <form className="mt-8 w-full max-w-md flex flex-col gap-4">
          <input type="text" placeholder={translations[language].name} className="p-2 border rounded" />
          <input type="email" placeholder={translations[language].email} className="p-2 border rounded" />
          <textarea placeholder={translations[language].message} className="p-2 border rounded h-24"></textarea>
          <Button className="bg-blue-500 text-white">{translations[language].send}</Button>
        </form>
      </main>
    </div>
  );
}
