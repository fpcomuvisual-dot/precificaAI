import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import WorkspacePage from "./components/WorkspacePage";
import PreviewPage from "./pages/PreviewPage";

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<WorkspacePage />} />
        <Route path="/preview" element={<PreviewPage />} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="bg-background-light min-h-screen max-w-[430px] mx-auto relative overflow-hidden shadow-2xl">
        <AnimatedRoutes />
      </div>
    </BrowserRouter>
  );
}
