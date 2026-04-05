/**
 * Client-side rPPG helper.
 * Extracts green channel mean from face ROI in video frames.
 * Actual HR estimation is done server-side for accuracy.
 */
export class RPPGClient {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;

  constructor() {
    this.canvas = document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d')!;
  }

  extractGreenChannel(video: HTMLVideoElement): number | null {
    if (!video.videoWidth) return null;

    this.canvas.width = video.videoWidth;
    this.canvas.height = video.videoHeight;
    this.ctx.drawImage(video, 0, 0);

    // Sample from center-upper region (approximate forehead)
    const x = Math.floor(video.videoWidth * 0.3);
    const y = Math.floor(video.videoHeight * 0.1);
    const w = Math.floor(video.videoWidth * 0.4);
    const h = Math.floor(video.videoHeight * 0.2);

    const imageData = this.ctx.getImageData(x, y, w, h);
    const data = imageData.data;

    let greenSum = 0;
    let count = 0;
    for (let i = 1; i < data.length; i += 4) {
      greenSum += data[i]; // green channel
      count++;
    }

    return count > 0 ? greenSum / count : null;
  }
}
