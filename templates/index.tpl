<html>
  <head>
    <title>rebuildd</title>
  </head>
  <body>
    <h2>rebuildd status on ${host}</h2>
      <table><tr><td>
      <table>
        <tr>
          <th>Id</th>
          <th>Package</th>
          <th>Version</th>
          <th>Distribution</th>
          <th>Arch</th>
          <th>Date</th>
          <th>Mail to</th>
          <th>Build status</th>
          <th>Host</th>
          <th>Build start</th>
          <th>Build end</th>
        </tr>
      % for job in jobs:
        <tr>
          <td><a href="/job_${job.id}">${job.id}</a></td>
          <td><a href="/package_${job.package.name}">${job.package.name}</a></td>
          <td><a href="/package_${job.package.name}/version_${job.package.version}">${job.package.version}</a></td>
          <td><a href="/dist_${job.dist}">${job.dist}</a></td>
          <td><a href="/arch_${job.arch}">${job.arch}</a></td>
          <td>${job.creation_date}</td>
          <td>${job.mailto}</td>
          % if job.build_status == 0:
            <td bgcolor="gray" align="center">UNKNOWN
          % endif
          % if job.build_status == 100:
            <td bgcolor="yellow" align="center">WAIT
          % endif
          % if job.build_status == 150:
            <td bgcolor="yellow" align="center">WAIT_LOCKED
          % endif
          % if job.build_status == 200:
            <td bgcolor="orange" align="center">BUILDING
          % endif
          % if job.build_status == 300:
            <td bgcolor="red" align="center">BUILD_FAILED
          % endif
          % if job.build_status == 400:
            <td bgcolor="green" align="center">BUILD_OK
          % endif
          % if job.build_status == 800:
            <td bgcolor="red" align="center">CANCELED
          % endif
          % if job.build_status == 900:
            <td bgcolor="red" align="center">FAILED
          % endif
          % if job.build_status == 1000:
            <td bgcolor="green" align="center">OK
          % endif
          <td><a href="/host_${job.host}">${job.host}</a></td>
          <td>${job.build_start}</td>
          <td>${job.build_end}</td>
          </td>
        </tr>
      % endfor
      </table></td><td valign="top"><img src="/build_stats.jpg"></td></tr></table>
  </body>
</html>
