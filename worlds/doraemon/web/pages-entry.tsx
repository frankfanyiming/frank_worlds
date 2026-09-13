import {createRoot} from 'react-dom/client';
import {Component, type ReactNode} from 'react';
import Page from './app/page';
import './app/globals.css';
import './app/xlands.css';
// Preserve the server-delivered homepage if the interactive shell cannot mount.
const root = document.getElementById('root')!;
const staticHome = root.innerHTML;
class HomeBoundary extends Component<{children: ReactNode}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() { return {failed: true}; }
  render() {
    return this.state.failed
      ? <div dangerouslySetInnerHTML={{__html: staticHome}} />
      : this.props.children;
  }
}
createRoot(root).render(<HomeBoundary><Page/></HomeBoundary>);
