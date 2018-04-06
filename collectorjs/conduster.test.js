import {Tracker} from './conduster';

test('Tracker.getEndFieldEventType should retrun right events depend on el.type', () => {
  let tracker = new Tracker('test-pixel-id');
  let types = {
    "file": "change",
    "submit": "click",
    "button": "click",
    "text": "blur",
    "textarea": "blur",
    "radio": "blur",
    "checkbox": "blur",
  }
  for (let t in types) {
    let el = {type: t};
    expect(tracker.getEndFieldEventType(el)).toBe(types[t]);
  }
});

const _getElementHelper = (type) => {
  let el = document.createElement('input');
  el.type = type;
  el.checked = false;
  el.readOnly = false;
  el.name = 'field-name';
  el.id = 'field-id';
  el.alt = 'field-alt';
  el.title = 'field-title';
  el.accessKey = 'l';
  el.className = 'field-css-class';
  el.spellcheck = true;
  el.style = { cssText: 'some style' };
  el.tabIndex = 1;
  el.value = 'field-value';
  el.event = new Tracker('test-pixel-id').initEvent('field-filled');
  return el;
}

test('Tracker.collectFieldFilledEvent should send data without nodata flag', () => {
  Tracker.prototype.collectEvent = jest.fn();
  let tracker = new Tracker('test-pixel-id', '',false);
  let el = _getElementHelper('text');
  tracker.collectFieldFilledEvent(el, 1);
  expect(Tracker.prototype.collectEvent.mock.calls.length).toBe(1);
  expect(Tracker.prototype.collectEvent.mock.calls[0][0].openData).toBe("field-value");
  expect(Tracker.prototype.collectEvent.mock.calls[0][0].hashData).toBe("9997ef5e83403936ae103c90c66757621c382d21");

});

test('Tracker.collectFieldFilledEvent shouldn\'t send data with nodata flag', () => {
  Tracker.prototype.collectEvent = jest.fn();
  let tracker = new Tracker('test-pixel-id', '', true);
  let el = _getElementHelper('text');
  tracker.collectFieldFilledEvent(el, 1);
  expect(Tracker.prototype.collectEvent.mock.calls.length).toBe(1);
  expect(Tracker.prototype.collectEvent.mock.calls[0][0].openData).toBe(undefined);
  expect(Tracker.prototype.collectEvent.mock.calls[0][0].hashData).toBe("9997ef5e83403936ae103c90c66757621c382d21");

});
