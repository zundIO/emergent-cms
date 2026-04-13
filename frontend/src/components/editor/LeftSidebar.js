import React from 'react';
import {
  FileText,
  Layers,
  Image,
  Settings,
  Rocket,
  HelpCircle,
  Plus,
  Users,
} from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '../../components/ui/tooltip';

const LeftSidebar = ({ activeSidebar, onSidebarClick, isAdmin }) => {
  const sidebarItems = [
    { id: 'pages', icon: FileText, label: 'Pages', enabled: true },
    { id: 'collections', icon: Layers, label: 'Collections', enabled: false },
    { id: 'assets', icon: Image, label: 'Assets', enabled: false },
    { id: 'settings', icon: isAdmin ? Users : Settings, label: isAdmin ? 'User Management' : 'Settings', enabled: isAdmin },
    { id: 'integration', icon: Rocket, label: 'Integration Guide', enabled: true },
  ];

  return (
    <TooltipProvider delayDuration={200}>
      <div className="left-sidebar" data-testid="editor-left-rail">
        {/* Add element button */}
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              data-testid="editor-left-rail-add-button"
              className="w-10 h-10 rounded-[4px] grid place-items-center mb-4 transition-colors duration-150"
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.14)',
                color: 'var(--primary-2)',
              }}
            >
              <Plus size={20} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Add Element</p>
          </TooltipContent>
        </Tooltip>

        {/* Separator */}
        <div
          className="w-6 h-px mb-3"
          style={{ backgroundColor: 'rgba(255, 255, 255, 0.06)' }}
        />

        {/* Navigation items */}
        <div className="flex flex-col gap-1 flex-1">
          {sidebarItems.map((item) => (
            <Tooltip key={item.id}>
              <TooltipTrigger asChild>
                <button
                  data-testid={`editor-left-rail-${item.id}-button`}
                  onClick={() => item.enabled && onSidebarClick(item.id)}
                  className="w-10 h-10 rounded-[4px] grid place-items-center transition-colors duration-150"
                  style={{
                    backgroundColor:
                      activeSidebar === item.id
                        ? 'rgba(16, 185, 129, 0.14)'
                        : 'transparent',
                    color:
                      activeSidebar === item.id
                        ? 'var(--primary-2)'
                        : item.enabled
                        ? 'var(--primary-fixed-dim)'
                        : 'var(--muted-2)',
                    opacity: item.enabled ? 1 : 0.5,
                    cursor: item.enabled ? 'pointer' : 'not-allowed',
                  }}
                >
                  <item.icon size={18} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p>{item.label}{!item.enabled ? ' (Coming Soon)' : ''}</p>
              </TooltipContent>
            </Tooltip>
          ))}
        </div>

        {/* Support button */}
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              data-testid="editor-left-rail-support-button"
              className="w-10 h-10 rounded-[4px] grid place-items-center mt-auto transition-colors duration-150"
              style={{
                color: 'var(--muted-2)',
              }}
            >
              <HelpCircle size={18} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Support</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
};

export default LeftSidebar;
