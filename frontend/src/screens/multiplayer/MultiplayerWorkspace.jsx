import React from "react";
import { SharedStatusBar } from "./SharedStatusBar";
import { Player1Workspace } from "./Player1Workspace";
import { Player2Workspace } from "./Player2Workspace";
import { Player3Workspace } from "./Player3Workspace";
import { useMultiplayerStore } from "../../store/useMultiplayerStore";

export function MultiplayerWorkspace() {
  const { myRole } = useMultiplayerStore();

  const renderRoleWorkspace = () => {
    switch (myRole) {
      case "player_1":
        return <Player1Workspace />;
      case "player_2":
        return <Player2Workspace />;
      case "player_3":
        return <Player3Workspace />;
      default:
        return <Player1Workspace />;
    }
  };

  return (
    <div className="space-y-6">
      <SharedStatusBar />
      <div className="max-w-7xl mx-auto px-4 py-2 animate-fade-in">
        {renderRoleWorkspace()}
      </div>
    </div>
  );
}
