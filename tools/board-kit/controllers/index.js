// Every controller of the board by the name its data-controller attribute uses. A new controller is
// a file in this folder and one line here.
import AgtermController from './agterm.js';
import ArtifactsController from './artifacts.js';
import ChartController from './chart.js';
import BacklogController from './backlog.js';
import ClockController from './clock.js';
import ColumnsController from './columns.js';
import CopyController from './copy.js';
import CursorController from './cursor.js';
import DrawerController from './drawer.js';
import EdgesController from './edges.js';
import FoldController from './fold.js';
import HotkeysController from './hotkeys.js';
import MarkdownController from './markdown.js';
import PanelController from './panel.js';
import PushController from './push.js';
import SearchController from './search.js';
import SheetController from './sheet.js';
import SplitterController from './splitter.js';
import StreamController from './stream.js';
import TipController from './tip.js';

export const CONTROLLERS = {
  agterm: AgtermController,
  artifacts: ArtifactsController,
  chart: ChartController,
  backlog: BacklogController,
  clock: ClockController,
  columns: ColumnsController,
  copy: CopyController,
  cursor: CursorController,
  drawer: DrawerController,
  edges: EdgesController,
  fold: FoldController,
  hotkeys: HotkeysController,
  markdown: MarkdownController,
  panel: PanelController,
  push: PushController,
  search: SearchController,
  sheet: SheetController,
  splitter: SplitterController,
  stream: StreamController,
  tip: TipController,
};
