// main.jsx — mount the stage
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <Stage width={900} height={600} duration={4.0} background="#1c1e22" persistKey="q4q9">
    <Scene />
  </Stage>
);
