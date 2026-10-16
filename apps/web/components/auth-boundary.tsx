"use client";
import {useEffect} from "react";
import {hasDemoAccess,isAuthStorageKey,getCurrentUserId} from "@/lib/demo-auth";
import {clearLearningBrowserState,migratePrivateReadingStorage} from "@/lib/learning-browser-storage";

export function AuthBoundary(){
 useEffect(()=>{
  if(hasDemoAccess())migratePrivateReadingStorage(localStorage,sessionStorage,getCurrentUserId());
  else clearLearningBrowserState(localStorage,sessionStorage);
  const reload=()=>{
   clearLearningBrowserState(localStorage,sessionStorage);
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
