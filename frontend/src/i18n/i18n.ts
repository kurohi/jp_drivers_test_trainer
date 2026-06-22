import i18n from "i18next"
import { initReactI18next } from "react-i18next"
import LanguageDetector from "i18next-browser-languagedetector"
import en from "./en.json"
import pt from "./pt.json"

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      pt: { translation: pt },
    },
    lng: "en",
    fallbackLng: "pt",
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: "jp-test-language",
    },
    interpolation: {
      escapeValue: false,
    },
  })

export default i18n