import React, { Component } from 'react';
import Chart from 'components/Chart';
import './App.css';

const masterstrack_url = 'http://localhost:8080/r/masterstrack';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {data: null};
  }

  async componentDidMount() {
    const params = 'event=60&agegroup=M50&year=2007-2018&season=Indoor';
    const resp = await fetch(`${masterstrack_url}/stats?${params}`);
    const data = await resp.json();
    this.setState({data});
  }

  render() {
    return (
      <div className="App">
        <Chart data={this.state.data}/>
     </div>
    );
  }
}

export default App;
