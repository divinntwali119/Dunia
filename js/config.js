/* Config and sensitive references should be kept minimal here.
   Actual secret values must be stored in /private/ and not pushed. */
window.__DUNIA_CONFIG = {
  ONESIGNAL_APP_ID: null
};

(async function(){
  try{
    const res = await fetch('/private/onesignal.json');
    if(res.ok){
      const json = await res.json();
      if(json.app_id) window.__DUNIA_CONFIG.ONESIGNAL_APP_ID = json.app_id;
    }
  }catch(e){}
})();
