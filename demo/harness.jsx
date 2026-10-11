// Mounts the three real widgets (feed, quick, strip) side by side in a normal page, the way Übersicht stacks them.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { css } from '@emotion/css';
import * as F from './widgets/feed.jsx';
import * as Q from './widgets/quick.jsx';
import * as S from './widgets/strip.jsx';

const rd = async (u) => (await fetch(u + '?' + Date.now())).text();
const [feed, rail, apps] = await Promise.all([rd('./data/feed.json'), rd('./data/rail.json'), rd('./data/apps.json')]);
const mount = (W, props, order) => {
  const el = document.createElement('div');
  el.className = css(W.className); el.style.position = 'absolute'; el.style.zIndex = order;
  document.getElementById('widgets').appendChild(el);
  createRoot(el).render(W.render(props, () => {}));
};
mount(S, { output: rail }, 1); mount(F, { output: feed, nav: {} }, 2); mount(Q, { output: apps }, 20);   // same stacking as Übersicht, quick on top
document.body.dataset.ready = '1';
