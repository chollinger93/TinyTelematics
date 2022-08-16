ThisBuild / resolvers ++= Seq(
  "Apache Development Snapshot Repository" at "https://repository.apache.org/content/repositories/snapshots/",
  Resolver.mavenLocal
)

name := "Flink Project"

version := "0.1-SNAPSHOT"

organization := "org.example"

ThisBuild / scalaVersion := "2.12.16"

val flinkVersion = "1.14.0"

val flinkDependencies = Seq(
  "org.apache.flink" %% "flink-scala"           % flinkVersion % "provided",
  "org.apache.flink" %% "flink-streaming-scala" % flinkVersion % "provided",
  "org.apache.flink" %% "flink-clients"         % flinkVersion % "provided"
)
libraryDependencies ++= Seq(
  "org.apache.flink" % "flink-connector-kafka" % "1.15.1",
  "io.estatico"     %% "newtype"               % "0.4.4",
  "tf.tofu"          % "derevo-core_2.12"      % "0.13.0",
  "tf.tofu"         %% "derevo-circe"          % "0.13.0",
  // Tests
  "org.scalactic" %% "scalactic"          % "3.2.10",
  "org.scalatest" %% "scalatest"          % "3.2.10" % Test,
  "org.scalatest" %% "scalatest-funsuite" % "3.2.10" % Test
)
val circeVersion = "0.14.2"
libraryDependencies ++= Seq(
  "io.circe" %% "circe-core",
  "io.circe" %% "circe-generic",
  "io.circe" %% "circe-parser"
).map(_ % circeVersion)

lazy val root = (project in file(".")).settings(
  libraryDependencies ++= flinkDependencies
)

assembly / mainClass := Some("org.example.Job")

// make run command include the provided dependencies
Compile / run := Defaults
  .runTask(
    Compile / fullClasspath,
    Compile / run / mainClass,
    Compile / run / runner
  )
  .evaluated

// stays inside the sbt console when we press "ctrl-c" while a Flink programme executes with "run" or "runMain"
Compile / run / fork := true
Global / cancelable := true

// exclude Scala library from assembly
assembly / assemblyOption := (assembly / assemblyOption).value
  .copy(includeScala = false)
// For newtypes
addCompilerPlugin(
  "org.scalamacros" % "paradise" % "2.1.1" cross CrossVersion.full
)
