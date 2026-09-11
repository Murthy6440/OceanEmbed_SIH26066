import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";

const Plot = createPlotlyComponent(Plotly);
export default Plot;

// Shared dark-theme layout defaults so every chart matches the dashboard.
export const baseLayout = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: { color: "#eaf2fa", size: 11.5 },
  margin: { l: 50, r: 16, t: 8, b: 40 },
  legend: {
    orientation: "h",
    y: -0.18,
    font: { size: 10.5 },
  },
  xaxis: {
    gridcolor: "#24405a",
    zerolinecolor: "#24405a",
    linecolor: "#24405a",
  },
  yaxis: {
    gridcolor: "#24405a",
    zerolinecolor: "#24405a",
    linecolor: "#24405a",
  },
};

export const baseConfig = {
  displayModeBar: false,
  responsive: true,
};
