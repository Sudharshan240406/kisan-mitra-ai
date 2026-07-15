import {
  LayoutDashboard, Cpu, Bot, Users, MessageSquare, Phone, MessageCircle,
  CloudSun, TrendingUp, Sprout, FlaskConical, Bug, Landmark, MapPin,
  Satellite, Tractor, BarChart3, FileText, BookOpen, Zap, Shield,
  Radio, Bell, Settings,
} from "lucide-react";

export type NavItem = {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  to: string;
  badge?: string;
};

export type NavGroup = { title: string; items: NavItem[] };

export const navGroups: NavGroup[] = [
  {
    title: "Command",
    items: [
      { icon: LayoutDashboard, label: "Overview", to: "/", badge: "Live" },
      { icon: Radio, label: "Mission Control", to: "/mission-control", badge: "IVR" },
      { icon: Cpu, label: "AI Platform", to: "/ai-platform" },
      { icon: Bot, label: "AI Agents", to: "/ai-agents", badge: "10" },
    ],
  },
  {
    title: "Farmers",
    items: [
      { icon: Users, label: "Farmers", to: "/farmers" },
      { icon: MessageSquare, label: "Conversations", to: "/conversations" },
      { icon: Phone, label: "Voice Calls", to: "/voice-calls" },
      { icon: MessageCircle, label: "SMS", to: "/sms" },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { icon: CloudSun, label: "Weather", to: "/weather" },
      { icon: TrendingUp, label: "Market Prices", to: "/market" },
      { icon: Sprout, label: "Crops", to: "/crops" },
      { icon: FlaskConical, label: "Soil Health", to: "/soil" },
      { icon: Bug, label: "Disease Detection", to: "/disease-detection" },
      { icon: Landmark, label: "Govt. Schemes", to: "/schemes" },
    ],
  },
  {
    title: "Geospatial",
    items: [
      { icon: MapPin, label: "GIS Map", to: "/gis-map" },
      { icon: Satellite, label: "Satellite", to: "/satellite" },
      { icon: Tractor, label: "Equipment", to: "/equipment" },
    ],
  },
  {
    title: "Ops",
    items: [
      { icon: BarChart3, label: "Analytics", to: "/analytics" },
      { icon: FileText, label: "Reports", to: "/reports" },
      { icon: BookOpen, label: "Knowledge", to: "/knowledge" },
      { icon: Zap, label: "Integrations", to: "/integrations" },
      { icon: Shield, label: "Governance", to: "/governance" },
      { icon: Radio, label: "Telemetry", to: "/telemetry" },
      { icon: Bell, label: "Alerts", to: "/alerts", badge: "4" },
      { icon: Settings, label: "Settings", to: "/settings" },
    ],
  },
];

export const flatNav: NavItem[] = navGroups.flatMap((g) => g.items);

export function findNav(path: string): NavItem | undefined {
  return flatNav.find((i) => i.to === path);
}
