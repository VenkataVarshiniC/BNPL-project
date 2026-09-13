import { Routes, Route, Outlet, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import Sidebar from "./components/Sidebar.jsx";
import TopBar from "./components/TopBar.jsx";
import PageTransition from "./components/PageTransition.jsx";
import { AssumptionsProvider } from "./state/assumptions.jsx";
import Landing from "./pages/Landing.jsx";
import Overview from "./pages/Overview.jsx";
import RiskAnalysis from "./pages/RiskAnalysis.jsx";
import Segmentation from "./pages/Segmentation.jsx";
import Profitability from "./pages/Profitability.jsx";
import RiskScore from "./pages/RiskScore.jsx";
import Optimization from "./pages/Optimization.jsx";
import Comparison from "./pages/Comparison.jsx";
import Decision from "./pages/Decision.jsx";
import Explainability from "./pages/Explainability.jsx";

const PAGE_META = {
  "/app": {
    title: "Executive summary",
    subtitle: "The net position, what is driving it, and what is recommended",
  },
  "/app/risk": {
    title: "Risk analysis",
    subtitle: "Loss attributed by merchant category, with drill-down",
  },
  "/app/profitability": {
    title: "Merchant category profitability",
    subtitle: "Fee revenue net of projected default losses",
  },
  "/app/segmentation": {
    title: "Customer segmentation",
    subtitle: "RFM-style cohorts by spend, frequency, and quality",
  },
  "/app/simulator": {
    title: "Strategy simulator",
    subtitle: "Approval threshold and assumptions vs projected net profit",
  },
  "/app/comparison": {
    title: "Scenario comparison",
    subtitle: "Strategies and baselines side by side on identical metrics",
  },
  "/app/decision": {
    title: "Decision summary",
    subtitle: "The problem, the recommendation, and what it costs",
  },
  "/app/risk-score": {
    title: "Default risk scoring",
    subtitle: "Score a proposed transaction before approval",
  },
  "/app/explainability": {
    title: "Explainability",
    subtitle: "SHAP feature contributions behind a risk score",
  },
};

function DashboardLayout() {
  const location = useLocation();
  const meta = PAGE_META[location.pathname] || PAGE_META["/app"];

  return (
    <div className="flex h-screen bg-ink overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar title={meta.title} subtitle={meta.subtitle} />
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <AnimatePresence mode="wait">
            <PageTransition key={location.pathname}>
              <Outlet />
            </PageTransition>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AssumptionsProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<DashboardLayout />}>
          <Route index element={<Overview />} />
          <Route path="risk" element={<RiskAnalysis />} />
          <Route path="profitability" element={<Profitability />} />
          <Route path="segmentation" element={<Segmentation />} />
          <Route path="simulator" element={<Optimization />} />
          <Route path="comparison" element={<Comparison />} />
          <Route path="decision" element={<Decision />} />
          <Route path="risk-score" element={<RiskScore />} />
          <Route path="explainability" element={<Explainability />} />
          {/* Old path kept so existing links and bookmarks don't 404 */}
          <Route path="optimization" element={<Optimization />} />
        </Route>
      </Routes>
    </AssumptionsProvider>
  );
}
