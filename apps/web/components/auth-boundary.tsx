"use client";
import {useEffect} from "react";
import {isAuthStorageKey} from "@/lib/demo-auth";

export function AuthBoundary(){
 useEffect(()=>{
  const reload=()=>{
   if(window.location.pathname==="/"||window.location.pathname.startsWith("/auth/"))return;
   // Discard all mounted owner-scoped state, including non-Chat workspaces.
   // eslint-disable-next-line @next/next/no-location-assign-relative-destination
   window.location.assign("/auth/login");
  };
  const storage=(event:StorageEvent)=>{if(isAuthStorageKey(event.key))reload();};
  window.addEventListener("luojia-auth-change",reload);window.addEventListener("storage",storage);
  return()=>{window.removeEventListener("luojia-auth-change",reload);window.removeEventListener("storage",storage);};
 },[]);
 return null;
}
