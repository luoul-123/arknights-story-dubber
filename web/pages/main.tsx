import React from "react";
import {createRoot} from "react-dom/client";
import Theater from "./theater";
import {setupStaticMedia} from "./static-media";
import "../app/globals.css";
import "./pages.css";

setupStaticMedia();
createRoot(document.getElementById("root")!).render(<Theater/>);
