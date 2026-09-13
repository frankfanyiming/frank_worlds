// SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
// SPDX-License-Identifier: MIT
// XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
import {createRoot} from 'react-dom/client';
import {Component, type ReactNode} from 'react';
import Page from './app/page';
import './app/globals.css';
import './app/xlands.css';
import './app/comic-home.css';
// Preserve the server-delivered homepage if the interactive shell cannot mount.
const root = document.getElementById('root')!;
const staticHome = root.innerHTML;
class HomeBoundary extends Component<{children: ReactNode}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() { return {failed: true}; }
  componentDidCatch() {
    const notice = document.getElementById('boot-recovery');
    if (notice) notice.hidden = false;
  }
  render() {
    return this.state.failed
      ? <div dangerouslySetInnerHTML={{__html: staticHome}} />
      : this.props.children;
  }
}
const appRoot = createRoot(root);
let recovered = false;
function recoverHome() {
  if (recovered) return;
  recovered = true;
  // Fatal errors can be reported while React is committing. Restore on the next task.
  setTimeout(() => {
    appRoot.unmount();
    root.innerHTML = staticHome;
    const notice = document.getElementById('boot-recovery');
    if (notice) notice.hidden = false;
  }, 0);
}
window.addEventListener('error', (event) => {
  if (event instanceof ErrorEvent && event.error) recoverHome();
});
window.addEventListener('unhandledrejection', recoverHome);
appRoot.render(<HomeBoundary><Page/></HomeBoundary>);
