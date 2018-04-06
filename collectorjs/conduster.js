import sha1 from 'sha1';
import Fingerprint2 from './fingerprint2';

const ZERO_TAB_INDEX = 100500;

const CORRECTION_KEYS = {
  "Backspace": true,
  "Delete": true,
  "Insert": true,
  // "Home": true,
  // "End": true,
  // "PageUp": true,
  // "PageDown": true,
  // "ArrowUp": true,
  // "ArrowDown": true,
  // "ArrowLeft": true,
  // "ArrowRight": true,
}

const SPECIAL_KEYS = {
  "Shift": true,
  "Control": true,
  "Meta": true,
  "ContextMenu": true,
  "Escape": true
}

const KEYDOWN_ELEMENT_TYPES = {
  "text": true,
  "textarea": true,
  "email": true,
  "password": true
}

const SUMBIT_ON_ENTER_TYPES = {
  "text": true,
  "email": true,
  "password": true,
  "select-multiple": true
}


export class Tracker {

  constructor(pixelId, apiHost, noData=false) {
    this.fp2 = new Fingerprint2({extendedJsFonts: true});
    this.pixelId = pixelId;
    this.noData = noData;
    this.apiUrl = "https://" + apiHost + "/collector/";
  }

  addEventListeners() {
    let form = document.getElementsByTagName("form")[0];
    let elements = this.sortedFormElements(form.elements);
    for (let i = 0; i < elements.length; i++) {
      this.addFieldEventListeners(elements[i], i);
    }
    this.addFormSubmitEventListeners(form);
  }

  /**
   * eventType - form-submitted
   * form.submit, window.beforeunload, (react-router???) - end
   * https://stackoverflow.com/questions/4570093/how-to-get-notified-about-changes-of-the-history-via-history-pushstate
   * @param form
   */
  addFormSubmitEventListeners (form) {
    form.currentLocation = window.location.href;
    form.submitInProgress = false;
    form.addEventListener('submit', (e) => {
      console.log('form submit', e);
      this.onFormSubmit(form);
    });

    // @todo: this two events: need to separate form submit from reload or url changing.
    // Maybe install pixel on thank you page

    window.addEventListener("beforeunload", (e) => {
      console.log('window beforeunload');
      this.onFormSubmit(form);
    });
    // history push state for react router https://stackoverflow.com/questions/4570093/how-to-get-notified-about-changes-of-the-history-via-history-pushstate
    (function(history){
        var pushState = history.pushState;
        history.pushState = function(state) {
            console.log('window history push state');
            this.onFormSubmit(form);

            return pushState.apply(history, arguments);
        };
    })(window.history);
  }

  onFormSubmit (form) {
    if(!form.submitInProgress) {
      form.submitInProgress = true;
      this.collectSubmitEvent(() => {
        form.submitInProgress = false;
      });
    }
  }

  collectSubmitEvent() {
    let event = this.initEvent('form-submitted');
    event.started = event.finished = new Date().getTime();
    event.duration = event.finished - event.started;
    this.collectEvent(event, null);
  }

  /**
   * return sorted by tabIndex elements array
   * @param elements HTMLCollection | iterable
   * @returns array
   */
  sortedFormElements(elements) {
    let res = [];
    for (let i = 0; i < elements.length; i++) {
      let el = elements[i];
      el.order = (el.tabIndex || ZERO_TAB_INDEX) + i;
      res.push(el);
    }
    res.sort((el1, el2) => {
      return el1.order - el2.order;
    });
    return res
  }

  /**
   * eventType - field-filled
   * input, textarea         focus - start; keydown, paste - middle; blur, (keydown enter???, form.submit???) - end
   * select, select-multiple focus - start; - middle; blur, (keydown enter???, form.submit???) - end
   * checkbox                focus - start; - middle; blur, (keydown enter???, form.submit???) - end
   * radio                   focus - start; - middle; blur, (keydown enter???, form.submit???) - end
   * file                    focus - start; - middle; change - end;
   * button                  focus - start; - middle; click - end;
   * @param el
   */
  addFieldEventListeners(el, i) {
    el.event = this.initEvent('field-filled');
    // started events
    el.addEventListener('focus', (e) => {
      el.event.started = new Date().getTime();
    });
    // middle events
    if (el.type in KEYDOWN_ELEMENT_TYPES) {
      el.addEventListener('keydown', (e) => {
        let event = el.event;
        if (e.key in CORRECTION_KEYS) {
          event.correctionCount++;
        }
        if (e.key in SPECIAL_KEYS) {
          event.specialKeypressCount++;
        }
        event.keypressCount++;
      });
      el.addEventListener('paste', (e) => {
        el.event.fromClipboard = true;
      });
    }
    // end events
    let endEventType = this.getEndFieldEventType(el);
    el.addEventListener(endEventType, (e) => {
      this.collectFieldFilledEvent(el, i+1);
    });
    if (el.type.toLowerCase() in SUMBIT_ON_ENTER_TYPES) {
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          this.collectFieldFilledEvent(el, i+1);
        }
      });
    }
  }

  collectFieldFilledEvent(el, fieldNumber) {
    if (!el.event.started) {
      el.event.started = new Date().getTime();
    }
    el.event.finished = new Date().getTime();
    el.event.duration = el.event.finished - el.event.started;
    let value = this.getElementValue(el);
    let normalizedValue = this.normalizeValue(value)
    el.event = Object.assign(el.event, {
      fieldType: el.type.toLowerCase(),
      fieldTag: el.tagName.toLowerCase(),
      fieldNumber: fieldNumber,
      fieldHidden: el.type === 'hidden',
      fieldChecked: el.checked,
      fieldReadonly: el.readOnly,
      fieldName: el.name,
      fieldId: el.id,
      fieldAlt: el.alt,
      fieldTitle: el.title,
      fieldData: JSON.stringify(el.dataset),
      fieldAccesskey: el.accessKey,
      fieldClass: el.className,
      fieldContenteditable: el.contentEditable,
      fieldContextmenu: el.contextMenu,
      fieldDir: el.dir,
      fieldLang: el.lang,
      fieldSpellcheck: el.spellcheck.toString(),
      fieldStyle: el.style.cssText,
      fieldTabindex: el.tabIndex,
      fieldRequired: el.required, // end ev
      fieldPattern: el.pattern, // end ev
      fieldList: this.getElementListAttr(el), // end ev
      textLength: value.length,
      openData: this.noData ? undefined : value,
      hashData: sha1(normalizedValue)
    });
    this.collectEvent(el.event);
  }

  normalizeValue(value) {
    return value.trim().toLowerCase()
  }

  collectEvent(event, then, async=true) {
    this.makeRequest('collect-event/', event, (res) => {
      if (then) { then(); }
    }, (err_code, err) => { console.warn(err_code, err) }, async);
  }

  initEvent(eventType) {
    return {
      session: this.sessionId,
      eventType: eventType,
      started: undefined,
      finished: undefined,
      duration: -1,
      fieldType: undefined,
      fieldNumber: undefined,
      fieldHidden: undefined,
      fieldChecked: undefined,
      fieldReadonly: undefined,
      fieldName: undefined,
      fieldId: undefined,
      fieldAlt: undefined,
      fieldTitle: undefined,
      fieldData: undefined,
      fieldAccesskey: undefined,
      fieldClass: undefined,
      fieldContenteditable: undefined,
      fieldContextmenu: undefined,
      fieldDir: undefined,
      fieldLang: undefined,
      fieldSpellcheck: undefined,
      fieldStyle: undefined,
      fieldTabindex: undefined,
      fieldRequired: undefined,
      fieldPattern: undefined,
      fieldList: undefined,
      correctionCount: 0,
      keypressCount: 0,
      specialKeypressCount: 0,
      textLength: 0,
      fromClipboard: false,
      openData: undefined,
      hashData: undefined
    }
  }

  /**
   * return event type for element
   * @param el - element
   * @returns {String}
   */
  getEndFieldEventType(el) {
    switch (el.type.toLowerCase()) {
      case 'file': return "change";
      case 'submit': case 'button': return 'click';
      default: return "blur";
    }
  }

  getElementListAttr(el) {
    if (!el.list) { return null; }
    let vals = [];
    let ops = el.list.options;
    for (let i = 0; i < ops.length; i++) {
      vals.push(ops[i].value);
    }
    return vals;
  }

  /**
   * return array of selected vals
   * @param el - select element
   * @returns {String}
   */
  getSelectValue(el) {
    let r = [], ops = el.options;
    for (let i = 0; i < ops.length; i++) {
      let o = el.options[i];
      if (o.selected) {
        r.push(o.text);
      }
    }
    return r.join('; ');
  }

  /**
   * return value of element
   * @param el - element
   * @returns {String|Array}
   */
  getElementValue(el) {
    switch (el.type) {
      case 'select-one':
      case 'select-multiple':
        return this.getSelectValue(el);
      case 'checkbox':
        return el.checked ? el.value : '';
      default:
        return el.value;
    }
  }

  makeRequest(urlFragment, params, then, reject = null, async=true) {
    const http = new XMLHttpRequest();
    http.open('POST', this.apiUrl + urlFragment, async);
    http.setRequestHeader('Content-type', 'application/json');
    http.send(JSON.stringify(params));

    http.onload = () => {
      if (http.status === 200) {
        then(JSON.parse(http.responseText));
      } else {
        if (reject) {
          let err_msg = '';
          try {
            err_msg = JSON.parse(http.responseText).error
          } catch (e) {
            err_msg = http.statusText;
          }
          reject(http.status, err_msg);
        }
      }
    }
    http.onerror = () => {
      if (reject) { reject(504, 'Connection timeout'); }
    }
  }

  formHasHidden() {
    let form = document.getElementsByTagName("form")[0];
    if (form.querySelectorAll('input[type=hidden]').length)
      return true;
    return false;
  }

  getData(then) {
    let form = document.getElementsByTagName("form")[0];
    let disabledFields = form.querySelectorAll('input[disabled=disabled]').length;
    let totalFields = form.querySelectorAll('input').length;
    let hiddenFields = form.querySelectorAll('input[type=hidden]').length;

    let data =  {
      pixelId: this.pixelId,
      userAgent: navigator.userAgent,
      cookieEnabled: navigator.cookieEnabled,
      currentLanguage: navigator.language,
      languages: navigator.languages,
      javaEnabled: navigator.javaEnabled(),
      online: navigator.onLine,
      timezoneOffset: new Date().getTimezoneOffset(),
      screenHeight: screen.height,
      screenWidth: screen.width,
      screenColorDepth: screen.colorDepth,
      location: document.location.href,
      referrer: document.referrer,
      pageTitle: document.title,
      hasHiddenFields: this.formHasHidden(),
      domain: document.location.origin,
      getParams: window.location.search.substr(1),
      viewPortHeight: document.documentElement.clientHeight,
      viewPortWidth: document.documentElement.clientWidth,
      avaliableHeight: window.innerHeight,
      avaliableWidth: window.innerWidth,
      pageTotal: 1,
      disabledFields: disabledFields,
      hiddenFields: hiddenFields,
      totalFields: totalFields
    }
    let started = new Date();
    this.fp2.get((components)=>{
      data.pluginList = components.plugins.join('; ');
      data.fonts = components.js_fonts;
      data.canvas = components.canvas;
      data.webglVendor = components.webgl_vendor;
      data.orientation = components.orientation;
      data.adBlock = components.adblock;
      data.hasSS = components.session_storage;
      data.hasLS = components.local_storage;
      data.hasIDB = components.indexed_db;
      data.hasODB = components.open_database;
      then(data)
    });

  }

  loadSession(then) {
    let sessionId = this.getCookie("trackSessionId");
    if (sessionId) {
      this.sessionId = sessionId;
      return then(sessionId);
    }
    this.openSession((sessionId) => {
      this.setCookie("trackSessionId", sessionId, 1);
      this.sessionId = sessionId;
      then(sessionId)
    })
  }

  openSession(then) {
    this.getData((data) => {
      this.makeRequest('open-session/', data, (res) => {
        if (then) { then(res.sessionId); }
      }, (err_code, err) => { console.warn(err_code, err) });
    });
  }

  setCookie(cname, cvalue, exdays) {
    let d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
  }

  getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
  }

  checkCookie(cookieName) {
    let cookie = this.getCookie(cookieName);
    if (cookie != "") {
      return true;
    } else {
      return false;
    }
  }

  track() {
    this.loadSession(() => {
      this.addEventListeners();
    })
  }

}

const init = (conf) => {
  let t = new Tracker(conf.cid, '{{ apiHost }}', conf.nodata);
  t.track();
}
if (window._cdrt) {
  init(window._cdrt);
}